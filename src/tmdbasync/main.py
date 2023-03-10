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
from tqdm import tqdm


class Tmdb:
    """TMDB Async."""

    naming_convention_map = {
        0: re.compile(r"^(?P<year>\d{4})\s{1}(?P<title>.+)$"),
        1: re.compile(r"^(?P<year>\d{4})\s{1}\-\s{1}(?P<title>.+)$"),
    }

    canoninput_schema = {
        "year": "int32",
        "title": str,
        "first_pass": "int32",
        "second_pass": "int32",
        "tmdb_id": "int32",
    }

    cast_schema = {
        "tmdb_id": "int32",
        "cast.adult": bool,
        "cast.gender": "int8",
        "cast.id": int,
        "cast.known_for_department": "category",
        "cast.name": str,
        "cast.original_name": str,
        "cast.popularity": float,
        "cast.profile_path": str,
        "cast.cast_id": "int8",
        "cast.character": str,
        "cast.credit_id": str,
        "cast.order": "int8",
    }

    crew_schema = {
        "tmdb_id": "int32",
        "crew.adult": bool,
        "crew.gender": "int8",
        "crew.id": int,
        "crew.known_for_department": "category",
        "crew.name": str,
        "crew.original_name": str,
        "crew.popularity": float,
        "crew.profile_path": str,
        "crew.credit_id": str,
        "crew.department": "category",
        "crew.job": str,
    }

    belongs_to_collection_schema = {
        "tmdb_id": "int32",
        "belongs_to_collection.id": int,
        "belongs_to_collection.name": str,
        "belongs_to_collection.poster_path": str,
        "belongs_to_collection.backdrop_path": str,
    }

    genres_schema = {
        "tmdb_id": "int32",
        "genres.id": "int8",
        "genres.name": str,
    }

    production_companies_schema = {
        "tmdb_id": "int32",
        "production_companies.id": "int32",
        "production_companies.logo_path": str,
        "production_companies.name": "category",
        "production_companies.origin_country": "category",
    }

    production_countries_schema = {
        "tmdb_id": "int32",
        "production_countries.iso_3166_1": "category",
        "production_countries.name": str,
    }

    spoken_languages_schema = {
        "tmdb_id": "int32",
        "spoken_languages.english_name": "category",
        "spoken_languages.iso_639_1": "category",
        "spoken_languages.name": str,
    }

    movie_details_schema = {
        "tmdb_id": "int32",
        "adult": bool,
        "backdrop_path": str,
        "budget": int,
        "homepage": str,
        "imdb_id": str,
        "original_language": "category",
        "original_title": str,
        "overview": str,
        "popularity": float,
        "poster_path": str,
        "release_date": "datetime64[ns]",
        "revenue": int,
        "runtime": "int16",
        "status": "category",
        "tagline": str,
        "title": str,
        "video": bool,
        "vote_average": float,
        "vote_count": "int16",
    }

    canon_input = pd.DataFrame(columns=[c for c in canoninput_schema.keys()])
    belongs_to_collection = pd.DataFrame(
        columns=[c for c in belongs_to_collection_schema.keys()]
    )
    cast = pd.DataFrame(columns=[c for c in cast_schema.keys()])
    crew = pd.DataFrame(columns=[c for c in crew_schema.keys()])
    genres = pd.DataFrame(columns=[c for c in genres_schema.keys()])
    movie_details = pd.DataFrame(columns=[c for c in movie_details_schema.keys()])
    production_companies = pd.DataFrame(
        columns=[c for c in production_companies_schema.keys()]
    )
    production_countries = pd.DataFrame(
        columns=[c for c in production_countries_schema.keys()]
    )
    spoken_languages = pd.DataFrame(columns=[c for c in spoken_languages_schema.keys()])

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
            tasks = []
            for t, y in zip(canon_input["title"], canon_input["year"], strict=True):
                if y == -1:
                    params = {"query": t}
                else:
                    params = {"query": t, "year": y}

                tasks.append(
                    session.get(
                        f"https://api.themoviedb.org/3/search/movie?api_key={self.tmdb_api_key}&language={self.language}&page=1&include_adult={self.include_adult}",
                        params=params,
                        ssl=False,
                    )
                )

            responses = [
                await f
                for f in tqdm(
                    asyncio.as_completed(tasks),
                    desc="{:<21}".format("searching TMDB ids"),
                    total=len(tasks),
                )
            ]
            for response in responses:
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
            tasks = [
                session.get(
                    f"https://api.themoviedb.org/3/movie/{tmdb_id}?api_key={self.tmdb_api_key}&language={self.language}",
                    ssl=False,
                )
                for tmdb_id in tmdb_ids
            ]

            responses = [
                await f
                for f in tqdm(
                    asyncio.as_completed(tasks),
                    desc="{:<21}".format("getting movie details"),
                    total=len(tasks),
                )
            ]
            for response in responses:
                if response.status == 200:
                    resp = await response.json()
                    tmdb_id = resp["id"]

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
                    self.genres = pd.concat([self.genres, genres], ignore_index=True)

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

                    resp["tmdb_id"] = resp.pop("id", None)

                    movie_details = pd.json_normalize(resp)
                    self.movie_details = self.movie_details.astype(
                        {"adult": bool, "video": bool}, errors="ignore"
                    )
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
            tasks = [
                session.get(
                    f"https://api.themoviedb.org/3/movie/{tmdb_id}/credits?api_key={self.tmdb_api_key}&language={self.language}",
                    ssl=False,
                )
                for tmdb_id in tmdb_ids
            ]

            responses = [
                await f
                for f in tqdm(
                    asyncio.as_completed(tasks),
                    desc="{:<21}".format("getting movie credits"),
                    total=len(tasks),
                )
            ]
            for response in responses:
                if response.status == 200:
                    resp = await response.json()
                    tmdb_id = resp["id"]

                    cast = pd.json_normalize(resp["cast"]).add_prefix("cast.")
                    cast["tmdb_id"] = tmdb_id
                    resp["cast"] = None
                    self.cast["cast.adult"] = self.cast["cast.adult"].astype(
                        bool, errors="ignore"
                    )
                    self.cast = pd.concat([self.cast, cast], ignore_index=True)

                    crew = pd.json_normalize(resp["crew"]).add_prefix("crew.")
                    crew["tmdb_id"] = tmdb_id
                    resp["crew"] = None
                    self.crew["crew.adult"] = self.crew["crew.adult"].astype(
                        bool, errors="ignore"
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
            "canon_input.csv": self.canon_input,
            "movie_details.csv": self.movie_details,
            "cast.csv": self.cast,
            "crew.csv": self.crew,
            "genres.csv": self.genres,
            "belongs_to_collection.csv": self.belongs_to_collection,
            "production_companies.csv": self.production_companies,
            "production_countries.csv": self.production_countries,
            "spoken_languages.csv": self.spoken_languages,
        }

        for k, v in filename_map.items():
            v.to_csv(
                (output_path / k),
                index=False,
                date_format="%Y-%m-%d",
                float_format="%.3f",
            )

    def generic_parse(self, queries: List[str]) -> None:
        """For a list of given queries, their TMDB IDs will be searched and used to lookup movie details and cast."""
        tmp_input = pd.DataFrame({"queries": queries})
        self.canon_input = tmp_input["queries"].str.extract(self.naming_convention)
        self.canon_input = self.canon_input.dropna(how="all").reset_index(drop=True)
        self.canon_input["year"] = self.canon_input["year"].fillna(-1)
        self.canon_input = self.canon_input.astype({"title": str, "year": int})

        self.canon_input["first_pass"] = asyncio.run(self.search_ids(self.canon_input))

        if self.backup_call is True:
            missing_tmdb_ids = self.canon_input[
                self.canon_input["first_pass"] == -1
            ].copy()
            missing_tmdb_ids["year"] = -1

            missing_tmdb_ids["second_pass"] = asyncio.run(
                self.search_ids(missing_tmdb_ids)
            )

            self.canon_input = self.canon_input.join(missing_tmdb_ids[["second_pass"]])
            self.canon_input["second_pass"] = self.canon_input["second_pass"].fillna(-1)
            self.canon_input["second_pass"] = self.canon_input["second_pass"].astype(
                "int"
            )

            self.canon_input["tmdb_id"] = np.where(
                self.canon_input["second_pass"] != -1,
                self.canon_input["second_pass"],
                self.canon_input["first_pass"],
            )
        else:
            self.canon_input["second_pass"] = -1
            self.canon_input["tmdb_id"] = self.canon_input["first_pass"]

        tmdb_ids = set(self.canon_input["tmdb_id"])

        asyncio.run(self.get_movie_details(tmdb_ids))
        asyncio.run(self.get_movie_credits(tmdb_ids))

        self._assign_types()

    def parse_movie_dirs(self, input_path: Path) -> None:
        """For a given input path, subfolders will be used for quering the TMDB for metadata."""
        if input_path.exists() is False:
            raise Exception("Please provide a valid INPUT_PATH!")
        input_folders = [f.name for f in input_path.iterdir() if f.is_dir()]
        self.generic_parse(input_folders)

    def _assign_types(self) -> None:

        self.canon_input = self.canon_input.astype(self.canoninput_schema)
        self.cast = self.cast.astype(self.cast_schema)
        self.crew = self.crew.astype(self.crew_schema)
        self.belongs_to_collection = self.belongs_to_collection.astype(
            self.belongs_to_collection_schema
        )
        self.genres = self.genres.astype(self.genres_schema)
        self.production_companies = self.production_companies.astype(
            self.production_companies_schema
        )
        self.production_countries = self.production_countries.astype(
            self.production_countries_schema
        )
        self.spoken_languages = self.spoken_languages.astype(
            self.spoken_languages_schema
        )
        self.movie_details = self.movie_details.astype(self.movie_details_schema)
