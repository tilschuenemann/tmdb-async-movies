"""TMDB Async, a Python package to asynchronously scrape movie metadata from the TMDB."""

import asyncio
import os
import re
from pathlib import Path
from typing import List
from typing import Set
from typing import Tuple

import aiohttp
import numpy as np
import pandas as pd


class Tmdb:
    """TMDB Async."""

    naming_convention_map = {
        0: re.compile(r"^(?P<year>\d{4})\s{1}(?P<title>.+)$"),
        1: re.compile(r"^(?P<year>\d{4})\s{1}\-\s{1}(?P<title>.+)$"),
    }
    canon_input = pd.DataFrame()

    belongs_to_collection = pd.DataFrame()
    cast = pd.DataFrame()
    crew = pd.DataFrame()
    genres = pd.DataFrame()
    movie_details = pd.DataFrame()
    production_companies = pd.DataFrame()
    production_countries = pd.DataFrame()
    spoken_languages = pd.DataFrame()

    def __init__(
        self,
        tmdb_api_key: str | None = None,
        include_adult: bool = True,
        language: str = "en_US",
        naming_convention: int = 0,
        backup_call: bool = True,
    ):
        """Initializes TMDB Async."""
        if tmdb_api_key is not None and len(tmdb_api_key) == 32:
            self.tmdb_api_key = tmdb_api_key
        elif (
            os.getenv("TMDB_API_KEY", "") != ""
            and len(os.getenv("TMDB_API_KEY", "")) == 32
        ):
            self.tmdb_api_key = os.getenv("TMDB_API_KEY", "")
        else:
            raise Exception(
                "Can't initialize tmdb, please provider a (proper) TMDB_API_KEY!"
            )

        if naming_convention not in self.naming_convention_map.keys():
            raise Exception("Please provide a proper NAMING_CONVENTION!")
        self.naming_convention = self.naming_convention_map[naming_convention]

        self.include_adult = include_adult
        self.language = language
        self.backup_call = backup_call

    async def search_ids(self, canon_input: pd.DataFrame) -> List[int]:
        """Given a canonical input TMDB IDs are searched.

        Canonical input is a dataframe with title and year column.
        """
        results: List[int] = []

        if canon_input.empty:
            return results

        async with aiohttp.ClientSession() as session:
            for t, y in zip(canon_input["title"], canon_input["year"], strict=True):
                if y is None:
                    params = {"query": t}
                else:
                    params = {"query": t, "year": y}
                async with session.get(
                    f"https://api.themoviedb.org/3/search/movie?api_key={self.tmdb_api_key}&language={self.language}&page=1&include_adult={self.include_adult}",
                    params=params,
                    ssl=False,
                ) as response:
                    if response.status == 200:
                        resp = await response.json()
                        try:
                            tmdb_id = resp["results"][0]["id"]
                        except IndexError:
                            tmdb_id = -1
                    else:
                        tmdb_id = -1
                    results.append(tmdb_id)
        return results

    async def get_movie_details(
        self, tmdb_ids: Set[int]
    ) -> Tuple[
        pd.DataFrame,
        pd.DataFrame,
        pd.DataFrame,
        pd.DataFrame,
        pd.DataFrame,
        pd.DataFrame,
    ]:
        """For a given set of TMDB IDs movie details are searched, stored and returned."""
        tmdb_ids = {t for t in tmdb_ids if t >= 0}

        async with aiohttp.ClientSession() as session:
            for tmdb_id in tmdb_ids:
                async with session.get(
                    f"https://api.themoviedb.org/3/movie/{tmdb_id}?api_key={self.tmdb_api_key}&language={self.language}",
                    ssl=False,
                ) as response:
                    if response.status == 200:
                        resp = await response.json()

                        if resp["belongs_to_collection"] is not None:
                            belongs_to_collection = pd.json_normalize(
                                resp["belongs_to_collection"],
                                record_prefix="belongs_to_collection.",
                            ).add_prefix("belongs_to_collection.")
                            belongs_to_collection["tmdb_id"] = tmdb_id
                            resp["belongs_to_collection"] = None
                        else:
                            belongs_to_collection = pd.DataFrame()
                        self.belongs_to_collection = pd.concat(
                            [self.belongs_to_collection, belongs_to_collection],
                            ignore_index=True,
                        )

                        genres = pd.json_normalize(resp["genres"]).add_prefix("genres.")
                        genres["tmdb_id"] = tmdb_id
                        resp["genres"] = None
                        self.genres = pd.concat(
                            [self.genres, genres], ignore_index=True
                        )

                        production_companies = pd.json_normalize(
                            resp["production_companies"],
                        ).add_prefix("production_companies.")
                        production_companies["tmdb_id"] = tmdb_id
                        resp["production_companies"] = None
                        self.production_companies = pd.concat(
                            [self.production_companies, production_companies],
                            ignore_index=True,
                        )

                        production_countries = pd.json_normalize(
                            resp["production_countries"],
                        ).add_prefix("production_countries.")
                        production_countries["tmdb_id"] = tmdb_id
                        resp["production_countries"] = None
                        self.production_countries = pd.concat(
                            [self.production_countries, production_countries],
                            ignore_index=True,
                        )

                        spoken_languages = pd.json_normalize(
                            resp["spoken_languages"]
                        ).add_prefix("spoken_languages.")
                        spoken_languages["tmdb_id"] = tmdb_id
                        resp["spoken_languages"] = None
                        self.spoken_languages = pd.concat(
                            [self.spoken_languages, spoken_languages], ignore_index=True
                        )

                        movie_details = pd.json_normalize(resp)
                        movie_details["tmdb_id"] = tmdb_id
                        self.movie_details = pd.concat(
                            [self.movie_details, movie_details], ignore_index=True
                        )
        return (
            self.belongs_to_collection,
            self.genres,
            self.production_companies,
            self.production_countries,
            self.spoken_languages,
            self.movie_details,
        )

    async def get_movie_credits(
        self, tmdb_ids: Set[int]
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """For a given set of TMDB IDs movie credits are searched, stored and returned."""
        tmdb_ids = {t for t in tmdb_ids if t >= 0}

        async with aiohttp.ClientSession() as session:
            for tmdb_id in tmdb_ids:
                async with session.get(
                    f"https://api.themoviedb.org/3/movie/{tmdb_id}/credits?api_key={self.tmdb_api_key}&language={self.language}",
                    ssl=False,
                ) as response:
                    if response.status == 200:
                        resp = await response.json()

                        cast = pd.json_normalize(resp["cast"]).add_prefix("cast.")
                        cast["tmdb_id"] = tmdb_id
                        resp["cast"] = None
                        if "cast.adult" in self.cast.columns:
                            self.cast["cast.adult"] = self.cast["cast.adult"].astype(
                                "bool"
                            )
                        self.cast = pd.concat([self.cast, cast], ignore_index=True)

                        crew = pd.json_normalize(resp["crew"]).add_prefix("crew.")
                        crew["tmdb_id"] = tmdb_id
                        resp["crew"] = None
                        if "crew.adult" in self.crew.columns:
                            self.crew["crew.adult"] = self.crew["crew.adult"].astype(
                                "bool"
                            )
                        self.crew = pd.concat([self.crew, crew], ignore_index=True)

        return (
            self.cast,
            self.crew,
        )

    def write(self, output_path: Path) -> None:
        """Writes all internal tables to output_path.

        Raises exception if output_path doesn't exist.
        """
        if output_path.exists() is False:
            raise Exception("Can't write data as OUTPUT_PATH doesn't exist!")

        filename_map = {
            "movie_details.csv": self.movie_details,
            "cast.csv": self.cast,
            "crew.csv": self.crew,
            "genres.csv": self.genres,
            "belongs_to_collection.csv": self.belongs_to_collection,
            "production_companies.csv": self.production_companies,
            "production_countries.csv": self.production_countries,
            "spoken_languages.csv": self.spoken_languages,
        }
        # TODO adress float and date format
        for k, v in filename_map.items():
            v.to_csv((output_path / k), index=False)

    def generic_parse(self, queries: List[str]) -> None:
        """For a list of given queries, their TMDB IDs will be searched and used to lookup movie details and cast."""
        tmp_input = pd.DataFrame({"queries": queries})
        self.canon_input = tmp_input["queries"].str.extract(self.naming_convention)
        self.canon_input = self.canon_input.dropna(how="all").reset_index(drop=True)
        self.canon_input = self.canon_input.astype({"title": str, "year": int})

        self.canon_input["tmdb_id"] = asyncio.run(self.search_ids(self.canon_input))

        if self.backup_call is True:
            missing_tmdb_ids = self.canon_input[
                self.canon_input["tmdb_id"] == -1
            ].copy()
            missing_tmdb_ids["year"] = None

            missing_tmdb_ids["backup_id"] = asyncio.run(
                self.search_ids(missing_tmdb_ids)
            )

            self.canon_input = self.canon_input.join(missing_tmdb_ids[["backup_id"]])
            self.canon_input["backup_id"] = self.canon_input["backup_id"].fillna(-1)
            self.canon_input["backup_id"] = self.canon_input["backup_id"].astype("int")

            self.canon_input["tmdb_id"] = np.where(
                self.canon_input["backup_id"] != -1,
                self.canon_input["backup_id"],
                self.canon_input["tmdb_id"],
            )

        tmdb_ids = set(self.canon_input["tmdb_id"])

        asyncio.run(self.get_movie_details(tmdb_ids))
        asyncio.run(self.get_movie_credits(tmdb_ids))

    def parse_movie_dirs(self, input_path: Path) -> None:
        """For a given input path, subfolders will be used for quering the TMDB for metadata."""
        if input_path.exists() is False:
            raise Exception("Please provide a valid INPUT_PATH!")
        input_folders = [f.name for f in input_path.iterdir() if f.is_dir()]
        self.generic_parse(input_folders)
