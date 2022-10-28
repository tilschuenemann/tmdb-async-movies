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
        root_movie_dir: str,
        output_path: pathlib.Path,
        tmdb_api_key: str = None,
        force_id_update: bool = False,
        strict: bool = False,
        parsing_style: int = 0,
        language: str = "en_US",
    ):
        self.ROOT_MOVIE_DIR = root_movie_dir
        self.OUTPUT_PATH = output_path
        self.TMDB_API_KEY = tmdb_api_key
        self.FORCE_ID_UPDATE = force_id_update
        self.STRICT = strict
        self.PARSING_STYLE = parsing_style
        self.LANGUAGE = language

        # error codes
        self.DEFAULT = 0
        self.NO_RESULT = -1
        self.NO_EXTRACT = -2

        # fallbacks
        if output_path is None:
            self.OUTPUT_PATH = pathlib.Path(os.getcwd())
        if tmdb_api_key is None:
            self.TMDB_API_KEY = os.getenv("TMDB_API_KEY")

        # setup internals
        self.setup_caches()
        self.read_existing()

    def setup_caches(self):
        tmp_path = self.OUTPUT_PATH / "mapping.csv"
        if tmp_path.exists():
            self.cached_mapping = pd.read_csv(tmp_path)
            self.cached_mapping["disk_path"] = self.cached_mapping["disk_path"].apply(lambda x: pathlib.Path(x))

            self.cached_metadata_ids = set(self.cached_mapping["tmdb_id"]) - set(
                [self.DEFAULT, self.NO_RESULT, self.NO_EXTRACT]
            )
        else:
            self.cached_mapping = pd.DataFrame()
            self.cached_metadata_ids = set()

    def read_existing(self):
        self.spoken_langs = (
            self.crew
        ) = self.cast = self.genres = self.prod_comp = self.prod_count = self.details = pd.DataFrame()

        read_map = dict(
            {
                "genres": self.genres,
                "crew": self.crew,
                "cast": self.cast,
                "spoken_languages": self.spoken_langs,
                "production_companies": self.prod_comp,
                "production_countries": self.prod_count,
                "details": self.details,
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
            self.genres,
            self.crew,
            self.cast,
            self.spoken_langs,
            self.prod_comp,
            self.prod_count,
            self.details,
        ) = df_list

    def parse(self):
        self.list_dirs()
        self.update_mapping()
        self.get_ids()
        self.update_lookup_ids()
        self.get_metadata()
        self.write()

    def list_dirs(self) -> pd.DataFrame:
        self.dirs = []
        for folder in self.ROOT_MOVIE_DIR.iterdir():
            if folder.is_dir():
                self.dirs.append(folder)

        self.mapping = pd.DataFrame(
            {
                "tmdb_id": pd.Series(dtype=int),
                "tmdb_id_man": pd.Series(dtype=int),
                "disk_path": pd.Series(dtype=str),
            }
        )
        self.mapping["disk_path"] = self.dirs

    def update_mapping(self):
        self.mapping = pd.concat([self.cached_mapping, self.mapping], axis=0, ignore_index=True).drop_duplicates(
            subset="disk_path", keep="first"
        )

    def get_id(self, title: str, year: int = -1) -> int:
        """Creates API request with title and year. If that fails,
        creates another with just the title (if STRICT=False).

        Returns -1 if no results come back.
        """
        if year != self.NO_RESULT:
            url = f"https://api.themoviedb.org/3/search/movie/?api_key={self.TMDB_API_KEY}&query={title}&year={year}&include_adult=true"
            response = requests.get(url).json()
            try:
                return response["results"][0]["id"]
            except IndexError:
                if self.STRICT is False:
                    return self.get_id(title=title, year=self.NO_RESULT)
                else:
                    return self.NO_RESULT
        else:
            url = f"https://api.themoviedb.org/3/search/movie/?api_key={self.TMDB_API_KEY}&query={title}&include_adult=true"
            response = requests.get(url).json()
            try:
                return response["results"][0]["id"]
            except IndexError:
                return self.NO_RESULT

    def get_ids(self):
        tmdb_man_ids = []
        tmdb_ids = []

        if self.PARSING_STYLE == 0:
            regex = re.compile(r"^(?P<disk_year>\d{4})\s{1}(?P<disk_title>.+)$")
        elif self.PARSING_STYLE == 1:
            regex = re.compile(r"^(?P<disk_year>\d{4})\s-\s(?P<disk_title>.+)$")
        else:
            exit("please supply a valid parsing style!")

        for index, row in tqdm(self.mapping.iterrows(), desc="getting ids", total=len(self.mapping.index)):
            tmdb_man_id = tmdb_id = self.DEFAULT

            if pd.isna(row["tmdb_id"]) or self.FORCE_ID_UPDATE or row["tmdb_id"] == self.DEFAULT:
                extract = re.match(regex, row["disk_path"].name)
                if extract is not None:
                    year = extract.groups("disk_year")[0]
                    title = extract.groups("disk_year")[1]
                    tmdb_id = self.get_id(title, year)
                else:
                    tmdb_id = self.NO_EXTRACT
            elif pd.notnull(row["tmdb_id_man"]):
                tmdb_id = row["tmdb_id"]
                tmdb_man_id = row["tmdb_id_man"]
            else:
                tmdb_id = row["tmdb_id"]

            path = row["disk_path"]

            tmdb_man_ids.append(tmdb_man_id)
            tmdb_ids.append(tmdb_id)

        self.mapping["tmdb_id"] = tmdb_ids
        self.mapping["tmdb_id_man"] = tmdb_man_ids

    def update_lookup_ids(self):
        self.lookup_ids = (set(self.mapping["tmdb_id"]) | set(self.mapping["tmdb_id_man"])) - set(
            self.cached_metadata_ids
        )

        if self.FORCE_ID_UPDATE is True:
            self.lookup_ids = set(self.mapping["tmdb_id"]) | set(self.mapping["tmdb_id_man"])

        self.lookup_ids -= set([self.DEFAULT, self.NO_RESULT, self.NO_EXTRACT])

    def get_metadata(self):

        for tmdb_id in tqdm(self.lookup_ids, desc="getting metadata"):

            if tmdb_id is False or tmdb_id <= 0:
                continue

            production_countries = (
                production_companies
            ) = genres = spoken_languages = cast = crew = details = pd.DataFrame()
            op_map = dict(
                {
                    "production_countries": production_countries,
                    "production_companies": production_companies,
                    "genres": genres,
                    "spoken_languages": spoken_languages,
                    "cast": cast,
                    "crew": crew,
                }
            )

            url = f"https://api.themoviedb.org/3/movie/{tmdb_id}?api_key={self.TMDB_API_KEY}&language={self.LANGUAGE}&append_to_response=credits"
            response = requests.get(url).json()

            df_store = []
            for k, v in op_map.items():
                if k in ["cast", "crew"]:
                    v = pd.json_normalize(response["credits"], record_path=k).add_prefix(f"{k}.")
                else:
                    v = pd.json_normalize(response, record_path=k).add_prefix(f"{k}.")
                    response.pop(k)
                v["tmdb_id"] = tmdb_id
                df_store.append(v)

            production_countries, production_companies, genres, spoken_languages, cast, crew = df_store

            response.pop("credits")
            details = pd.json_normalize(
                response,
                errors="ignore",
            ).add_prefix("m.")
            details["tmdb_id"] = details.pop("m.id")

            # append new metadata
            self.details = pd.concat([self.details, details], axis=0, ignore_index=True)
            self.cast = pd.concat([self.cast, cast], axis=0, ignore_index=True)
            self.crew = pd.concat([self.crew, crew], axis=0, ignore_index=True)
            self.genres = pd.concat([self.genres, genres], axis=0, ignore_index=True)
            self.spoken_langs = pd.concat([self.spoken_langs, spoken_languages], axis=0, ignore_index=True)
            self.prod_count = pd.concat(
                [self.prod_count, production_countries],
                axis=0,
                ignore_index=True,
            )
            self.prod_comp = pd.concat(
                [self.prod_comp, production_companies],
                axis=0,
                ignore_index=True,
            )

    def write(self):
        write_map = dict(
            {
                "mapping.csv": self.mapping,
                "details.csv": self.details,
                "spoken_languages.csv": self.spoken_langs,
                "crew.csv": self.crew,
                "cast.csv": self.cast,
                "genres.csv": self.genres,
                "production_companies.csv": self.prod_comp,
                "production_countries.csv": self.prod_count,
            }
        )

        for fname, df in write_map.items():
            tmp_path = self.OUTPUT_PATH / fname
            df.to_csv(tmp_path, date_format="%Y-%m-%d", index=False)
