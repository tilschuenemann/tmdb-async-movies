import pandas as pd
import numpy as np
from tqdm import tqdm

import json
import os
import pathlib
import re
import requests


class movieparse:
    def __init__(
        self,
        root_movie_dir: pathlib.Path,
        output_path: pathlib.Path,
        tmdb_api_key: str = None,
        force_id_update: bool = False,
        force_metadata_update: bool = False,
        strict: bool = False,
        parsing_style: int = 0,
        language: str = "en_US",
    ):
        self.ROOT_MOVIE_DIR = root_movie_dir
        self.OUTPUT_PATH = output_path
        self.TMDB_API_KEY = tmdb_api_key
        self.FORCE_ID_UPDATE = force_id_update
        self.FORCE_METADATA_UPDATE = force_metadata_update
        self.STRICT = strict
        self.PARSING_STYLE = parsing_style
        self.LANGUAGE = language

        # error codes
        self.__DEFAULT = 0
        self.__NO_RESULT = -1
        self.__NO_EXTRACT = -2
        self.__BAD_RESPONSE = -3

        # fallbacks and error handling
        if output_path is None:
            self.OUTPUT_PATH = pathlib.Path(os.getcwd())
        elif output_path.is_dir() is False:
            exit("please supply a ROOT_MOVIE_DIR that is a directory!")

        if tmdb_api_key is None:
            if os.getenv("TMDB_API_KEY") is not None:
                self.TMDB_API_KEY = os.getenv("TMDB_API_KEY")
            else:
                exit("please supply a TMDB_API_KEY!")

        if self.PARSING_STYLE not in range(0, 2):
            exit("please supply a valid PARSING_STYLE!")

        # setup internals
        self._setup_caches()
        self._read_existing()

    def _setup_caches(self):
        self.cached_mapping_ids = set()
        self.cached_mapping = pd.DataFrame()

        tmp_path = self.OUTPUT_PATH / "mapping.csv"
        if tmp_path.exists():
            self.cached_mapping = pd.read_csv(tmp_path)
            self.cached_mapping["disk_path"] = self.cached_mapping["disk_path"].apply(lambda x: pathlib.Path(x))
            self.cached_mapping_ids = set(self.cached_mapping["tmdb_id"])

    def _read_existing(self):
        """Reads metadata CSVs if existing and appends tmdb_ids to cached_metadata_ids."""

        self.cached_metadata_ids = set()
        self.cast = (
            self.collect
        ) = (
            self.crew
        ) = self.details = self.genres = self.prod_comp = self.prod_count = self.spoken_langs = pd.DataFrame()

        read_map = dict(
            {
                "cast": self.cast,
                "collections": self.collect,
                "crew": self.crew,
                "details": self.details,
                "genres": self.genres,
                "production_companies": self.prod_comp,
                "production_countries": self.prod_count,
                "spoken_languages": self.spoken_langs,
            }
        )
        df_list = []
        for fname, df in read_map.items():
            tmp_path = self.OUTPUT_PATH / f"{fname}.csv"
            if tmp_path.exists():
                df = pd.read_csv(tmp_path)
                self.cached_metadata_ids |= set(df["tmdb_id"])
            df_list.append(df)

        (
            self.cast,
            self.collect,
            self.crew,
            self.details,
            self.genres,
            self.prod_comp,
            self.prod_count,
            self.spoken_langs,
        ) = df_list

    def parse(self):
        self._list_dirs()
        self._update_mapping()
        self._get_ids()
        self._update_metadata_lookup_ids()
        self._get_metadata()

    def _list_dirs(self) -> pd.DataFrame:
        dirs = []
        for folder in self.ROOT_MOVIE_DIR.iterdir():
            if folder.is_dir():
                dirs.append(folder)

        self.mapping = pd.DataFrame(
            {
                "tmdb_id": self.__DEFAULT,
                "tmdb_id_man": self.__DEFAULT,
                "disk_path": dirs,
            }
        )

    def _update_mapping(self):
        self.mapping = pd.concat([self.cached_mapping, self.mapping], axis=0, ignore_index=True).drop_duplicates(
            subset="disk_path", keep="first"
        )

    def _get_id(self, title: str, year: int = -1) -> int:
        """Creates API request with title and year. If that fails,
        creates another with just the title (if STRICT=False).

        Returns -1 if no results come back.
        """
        if year != self.__NO_RESULT:
            url = f"https://api.themoviedb.org/3/search/movie/?api_key={self.TMDB_API_KEY}&query={title}&year={year}&include_adult=true"
            response = requests.get(url).json()
            try:
                return response["results"][0]["id"]
            except IndexError:
                if self.STRICT is False:
                    return self._get_id(title=title, year=self.__NO_RESULT)
                else:
                    return self.__NO_RESULT
        else:
            url = f"https://api.themoviedb.org/3/search/movie/?api_key={self.TMDB_API_KEY}&query={title}&include_adult=true"
            response = requests.get(url).json()
            try:
                return response["results"][0]["id"]
            except IndexError:
                return self.__NO_RESULT

    def _get_ids(self):
        tmdb_ids = []

        if self.PARSING_STYLE == 0:
            regex = re.compile(r"^(?P<disk_year>\d{4})\s{1}(?P<disk_title>.+)$")
        elif self.PARSING_STYLE == 1:
            regex = re.compile(r"^(?P<disk_year>\d{4})\s-\s(?P<disk_title>.+)$")

        for index, row in tqdm(self.mapping.iterrows(), desc="getting ids", total=len(self.mapping.index)):
            tmdb_id = self.__DEFAULT

            if row["tmdb_id"] == self.__DEFAULT or self.FORCE_ID_UPDATE:
                extract = re.match(regex, row["disk_path"].name)
                if extract is not None:
                    year = extract.groups("disk_year")[0]
                    title = extract.groups("disk_year")[1]
                    try:
                        tmdb_id = self._get_id(title, year)
                    except:
                        tmdb_id = self.__BAD_RESPONSE
                else:
                    tmdb_id = self.__NO_EXTRACT
            else:
                tmdb_id = row["tmdb_id"]

            tmdb_ids.append(tmdb_id)

        self.mapping["tmdb_id"] = tmdb_ids
        self.mapping.to_csv((self.OUTPUT_PATH / "mapping.csv"), date_format="%Y-%m-%d", index=False)

    def _update_metadata_lookup_ids(self):
        self.metadata_lookup_ids = set(self.mapping["tmdb_id"]) | set(self.mapping["tmdb_id_man"])

        if self.FORCE_METADATA_UPDATE is False:
            self.metadata_lookup_ids -= set(self.cached_metadata_ids)

        self.metadata_lookup_ids -= set([self.__DEFAULT, self.__NO_RESULT, self.__NO_EXTRACT, self.__BAD_RESPONSE])

    def _dissect_metadata_response(self, response: dict, tmdb_id: int):
        cast = collect = crew = genres = prod_comp = prod_count = spoken_langs = pd.DataFrame()

        op_map = dict(
            {
                "cast": cast,
                "collection": collect,
                "crew": crew,
                "genres": genres,
                "production_companies": prod_comp,
                "production_countries": prod_count,
                "spoken_languages": spoken_langs,
            }
        )
        df_store = []
        for k, df in op_map.items():
            if k in ["cast", "crew"]:
                df = pd.json_normalize(response["credits"], record_path=k).add_prefix(f"{k}.")
            elif k == "collection":
                try:
                    if response["belongs_to_collection"] is None:
                        response.pop("belongs_to_collection")
                    else:
                        df = pd.json_normalize(response["belongs_to_collection"], errors="ignore").add_prefix(f"{k}.")
                        response.pop("belongs_to_collection")
                except Exception as e:
                    print("The error raised is: ", e)
            else:
                df = pd.json_normalize(response, record_path=k).add_prefix(f"{k}.")
                response.pop(k)
            df["tmdb_id"] = tmdb_id
            df_store.append(df)

        cast, collect, crew, genres, prod_comp, prod_count, spoken_langs = df_store

        response.pop("credits")
        details = pd.json_normalize(
            response,
            errors="ignore",
        ).add_prefix("m.")
        details["tmdb_id"] = details.pop("m.id")

        if cast.empty is False:
            self.cast = pd.concat([self.cast, cast], axis=0, ignore_index=True)
        self.collect = pd.concat([self.collect, collect], axis=0, ignore_index=True)
        if crew.empty is False:
            self.crew = pd.concat([self.crew, crew], axis=0, ignore_index=True)
        self.details = pd.concat([self.details, details], axis=0, ignore_index=True)
        self.genres = pd.concat([self.genres, genres], axis=0, ignore_index=True)
        self.spoken_langs = pd.concat([self.spoken_langs, spoken_langs], axis=0, ignore_index=True)

        self.prod_comp = pd.concat(
            [self.prod_comp, prod_comp],
            axis=0,
            ignore_index=True,
        )
        self.prod_count = pd.concat(
            [self.prod_count, prod_count],
            axis=0,
            ignore_index=True,
        )

    def _get_metadata(self):

        for tmdb_id in tqdm(self.metadata_lookup_ids, desc="getting metadata"):
            url = f"https://api.themoviedb.org/3/movie/{tmdb_id}?api_key={self.TMDB_API_KEY}&language={self.LANGUAGE}&append_to_response=credits"
            response = requests.get(url).json()
            self._dissect_response(response, tmdb_id)

    def write(self):
        write_map = dict(
            {
                "details.csv": self.details,
                "spoken_languages.csv": self.spoken_langs,
                "crew.csv": self.crew,
                "cast.csv": self.cast,
                "genres.csv": self.genres,
                "production_companies.csv": self.prod_comp,
                "production_countries.csv": self.prod_count,
                "collections.csv": self.collect,
            }
        )

        for fname, df in write_map.items():
            tmp_path = self.OUTPUT_PATH / fname
            if df.empty is False:
                df.to_csv(tmp_path, date_format="%Y-%m-%d", index=False)
