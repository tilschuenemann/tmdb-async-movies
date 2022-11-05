import pandas as pd
from tqdm import tqdm

import os
import pathlib
import re
import requests
from typing import Set, Optional, Dict, List, Union

from movieparse.type_mapping import movieparse_types


class movieparse:
    mapping = pd.DataFrame()
    cast = collect = crew = details = genres = prod_comp = prod_count = spoken_langs = pd.DataFrame()
    cached_mapping_ids: Set[int] = set()
    cached_metadata_ids: Set[int] = set()
    cached_mapping = pd.DataFrame()

    # default codes
    __DEFAULT = 0
    __NO_RESULT = -1
    __NO_EXTRACT = -2
    __BAD_RESPONSE = -3

    @staticmethod
    def get_parsing_patters() -> dict[int, re.Pattern]:
        return {
            0: re.compile(r"^(?P<disk_year>\d{4})\s{1}(?P<disk_title>.+)$"),
            1: re.compile(r"^(?P<disk_year>\d{4})\s-\s(?P<disk_title>.+)$"),
        }

    def __init__(
        self,
        root_movie_dir: pathlib.Path | None = None,
        output_path: pathlib.Path | None = None,
        movie_list: List[str] | None = None,
        tmdb_api_key: str | None = None,
        parsing_style: int = -1,
        force_id_update: bool = False,
        force_metadata_update: bool = False,
        strict: bool = False,
        language: str = "en_US",
    ):

        self.__FORCE_ID_UPDATE = force_id_update
        self.__FORCE_METADATA_UPDATE = force_metadata_update
        self.__STRICT = strict
        self.__LANGUAGE = language

        if (root_movie_dir is None and movie_list is None) or (
            root_movie_dir is not None
            and movie_list is not None
            and (root_movie_dir.is_dir() is False or not movie_list)
        ):
            exit("please supply a ROOT_MOVIE_DIR or a MOVIE_LIST!")
        else:
            self.__ROOT_MOVIE_DIR = root_movie_dir
            self.__MOVIE_LIST = movie_list

        if output_path is None:
            output_path = pathlib.Path(os.getcwd())
        elif output_path.is_dir() is False:
            exit("please supply a ROOT_MOVIE_DIR that is a directory!")
        self.__OUTPUT_PATH = output_path

        if tmdb_api_key is None and os.getenv("TMDB_API_KEY") is not None:
            self.__TMDB_API_KEY = os.getenv("TMDB_API_KEY")
        elif tmdb_api_key is not None:
            self.__TMDB_API_KEY = tmdb_api_key
        else:
            exit("please supply a TMDB_API_KEY!")

        if parsing_style not in range(-1, max(movieparse.get_parsing_patters().keys())):
            exit("please supply a valid PARSING_STYLE!")
        else:
            self.__PARSING_STYLE = parsing_style

        # setup internals
        self._setup_caches()
        self._read_existing()

    def _table_iter(self) -> dict[str, pd.DataFrame]:
        return {
            "cast": self.cast,
            "collection": self.collect,
            "crew": self.crew,
            "genres": self.genres,
            "production_companies": self.prod_comp,
            "production_countries": self.prod_count,
            "spoken_languages": self.spoken_langs,
            "details": self.details,
        }

    def _setup_caches(self) -> None:
        tmp_path = self.__OUTPUT_PATH / "mapping.csv"
        if tmp_path.exists():
            self.cached_mapping = pd.read_csv(tmp_path)
            self.cached_mapping["disk_path"] = self.cached_mapping["disk_path"].apply(lambda x: pathlib.Path(x))
            self.cached_mapping_ids = set(self.cached_mapping["tmdb_id"])

    def _read_existing(self) -> None:
        """Reads metadata CSVs if existing and appends tmdb_ids to cached_metadata_ids."""
        df_list = []
        for fname, df in self._table_iter().items():
            tmp_path = self.__OUTPUT_PATH / f"{fname}.csv"
            if tmp_path.exists():
                df = pd.read_csv(tmp_path)
                self.cached_metadata_ids |= set(df["tmdb_id"])
                df = pd.DataFrame(movieparse_types(df.to_dict()))  # type: ignore
            else:
                df = pd.DataFrame()
            df_list.append(df)

        (
            self.cast,
            self.collect,
            self.crew,
            self.genres,
            self.prod_comp,
            self.prod_count,
            self.spoken_langs,
            self.details,
        ) = df_list

    def parse(self) -> None:
        self._create_mapping()

        if self.__PARSING_STYLE == -1:
            self._guess_parsing_style()

        self._update_mapping()
        self._get_ids()
        self._update_metadata_lookup_ids()
        self._get_metadata()

    def _create_mapping(self) -> None:
        if self.__MOVIE_LIST is None and isinstance(self.__ROOT_MOVIE_DIR, pathlib.Path):
            names = []
            for folder in self.__ROOT_MOVIE_DIR.iterdir():
                if folder.is_dir():
                    names.append(folder)
            self.mapping = pd.DataFrame(
                {
                    "tmdb_id": self.__DEFAULT,
                    "tmdb_id_man": self.__DEFAULT,
                    "disk_path": names,
                }
            )
        elif self.__ROOT_MOVIE_DIR is None:
            self.mapping = pd.DataFrame(
                {
                    "tmdb_id": self.__DEFAULT,
                    "tmdb_id_man": self.__DEFAULT,
                    "disk_path": self.__MOVIE_LIST,
                }
            )

    def _guess_parsing_style(self) -> None:
        """Iterates over supplied names with all parsing styles, determining the most matches. Incase two patterns have
        the same matches, the first one is used."""

        tmp = pd.DataFrame()
        if self.__MOVIE_LIST is None:
            tmp["names"] = self.mapping["disk_path"].apply(lambda x: pathlib.Path(x).name)
        elif self.__ROOT_MOVIE_DIR is None:
            tmp["names"] = self.mapping["disk_path"]

        max_matches = 0
        for style, pattern in movieparse.get_parsing_patters().items():
            matches = tmp["names"].str.extract(pattern, expand=True).notnull().sum().sum()
            if matches > max_matches:
                self.__PARSING_STYLE = style
                max_matches = matches

        if max_matches == 0 and self.__PARSING_STYLE == -1:
            exit("couldn't estimate a parsing style, please supply one for yourself!")

        max_items = len(tmp.index) * 2
        print(f"estimated best parsing style: {self.__PARSING_STYLE} with {max_matches} / {max_items} matches")

    def _update_mapping(self) -> None:
        self.mapping = pd.concat([self.cached_mapping, self.mapping], axis=0, ignore_index=True).drop_duplicates(
            subset="disk_path", keep="first"
        )

    def _get_id(self, title: str, year: int = -1) -> int:
        """Creates API request with title and year. If that fails,
        creates another with just the title (if STRICT=False).

        Returns -1 if no results come back.
        """
        if year == self.__NO_RESULT:
            response = requests.get(
                f"https://api.themoviedb.org/3/search/movie/?api_key={self.__TMDB_API_KEY}&query={title}&year={year}&include_adult=true"
            ).json()
            try:
                return int(response["results"][0]["id"])
            except IndexError:
                if self.__STRICT is True:
                    return self.__NO_RESULT
            except KeyError:
                return self.__BAD_RESPONSE

        response = requests.get(
            f"https://api.themoviedb.org/3/search/movie/?api_key={self.__TMDB_API_KEY}&query={title}&include_adult=true"
        ).json()
        try:
            return int(response["results"][0]["id"])
        except IndexError:
            return self.__NO_RESULT
        except KeyError:
            return self.__BAD_RESPONSE

    def _get_ids(self) -> None:
        tmdb_ids = []

        regex = movieparse.get_parsing_patters()[self.__PARSING_STYLE]

        for index, row in tqdm(self.mapping.iterrows(), desc="getting ids", total=len(self.mapping.index)):
            tmdb_id = self.__DEFAULT

            if row["tmdb_id"] == self.__DEFAULT or self.__FORCE_ID_UPDATE:
                extract = re.match(regex, row["disk_path"].name)
                if extract is not None:
                    year = int(extract.group("disk_year"))
                    title = extract.group("disk_title")
                    tmdb_id = self._get_id(title, year)
                else:
                    tmdb_id = self.__NO_EXTRACT
            else:
                tmdb_id = row["tmdb_id"]

            tmdb_ids.append(tmdb_id)

        self.mapping["tmdb_id"] = tmdb_ids
        self.mapping.to_csv((self.__OUTPUT_PATH / "mapping.csv"), date_format="%Y-%m-%d", index=False)

    def _update_metadata_lookup_ids(self) -> None:
        self.metadata_lookup_ids = set(self.mapping["tmdb_id"]) | set(self.mapping["tmdb_id_man"])

        if self.__FORCE_METADATA_UPDATE is False:
            self.metadata_lookup_ids -= set(self.cached_metadata_ids)

        self.metadata_lookup_ids -= set([self.__DEFAULT, self.__NO_RESULT, self.__NO_EXTRACT, self.__BAD_RESPONSE])

    def _dissect_metadata_response(self, response: Dict[str, pd.DataFrame], tmdb_id: int) -> None:
        results = []
        for c, df in self._table_iter().items():
            tmp = pd.DataFrame()

            if c in ["cast", "crew"]:
                tmp = pd.json_normalize(response["credits"], record_path=c).add_prefix(f"{c}.")
            elif c == "collection":
                if response["belongs_to_collection"] is not None:
                    tmp = pd.json_normalize(response["belongs_to_collection"]).add_prefix(f"{c}.")
                response.pop("belongs_to_collection")
            elif c == "details":
                response.pop("credits")
                response.pop("id")
                tmp = pd.json_normalize(response)
            else:
                tmp = pd.json_normalize(response, record_path=c).add_prefix(f"{c}.")
                response.pop(c)

            tmp["tmdb_id"] = tmdb_id
            tmp = pd.DataFrame(movieparse_types(tmp.to_dict()))  # type: ignore

            if tmp.empty is False:
                df = pd.concat([df, tmp], axis=0, ignore_index=True)
            results.append(df)
        (
            self.cast,
            self.collect,
            self.crew,
            self.genres,
            self.prod_comp,
            self.prod_count,
            self.spoken_langs,
            self.details,
        ) = results

    def _get_metadata(self) -> None:
        for tmdb_id in tqdm(self.metadata_lookup_ids, desc="getting metadata"):
            url = f"https://api.themoviedb.org/3/movie/{tmdb_id}?api_key={self.__TMDB_API_KEY}&language={self.__LANGUAGE}&append_to_response=credits"
            response = requests.get(url).json()
            self._dissect_metadata_response(response, tmdb_id)

    def write(self) -> None:
        for fname, df in self._table_iter().items():
            tmp_path = self.__OUTPUT_PATH / f"{fname}.csv"
            if df.empty is False:
                df.to_csv(tmp_path, date_format="%Y-%m-%d", index=False)
