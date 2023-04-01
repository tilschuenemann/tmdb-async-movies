"""tmdbasyncmovies, a Python package to asynchronously scrape movie metadata from the TMDB."""
import asyncio
import os
import re
import urllib.parse
from pathlib import Path
from typing import Dict
from typing import List
from typing import Set

import aiohttp
import numpy as np
import pandas as pd
import tqdm
from aiohttp_retry import ExponentialRetry
from aiohttp_retry import RetryClient


class TmdbAsyncMovies:
    """TMDB Async Movies."""

    def __init__(
        self,
        tmdb_api_key: str | None = None,
        include_adult: bool = True,
        language: str = "en_US",
        naming_convention: int = 0,
        backup_call: bool = True,
    ):
        """Initializes TMDB Async.

        Args:
          tmdb_api_key: TMDB API Key. Falls back to environment variable TMDB_API_KEY if not specified.
          include_adult: Whether to include adult results.
          language: ISO-639-1 shortcode for getting locale information.
          naming_convention: Naming convention used for extracting title and year.
          backup_call: Whether to submit another query using title only if title + year yields no result.
        """
        if tmdb_api_key is not None and len(tmdb_api_key) == 32:
            self.tmdb_api_key = tmdb_api_key
        elif os.getenv("TMDB_API_KEY", "") != "" and len(os.getenv("TMDB_API_KEY", "")) == 32:
            self.tmdb_api_key = os.getenv("TMDB_API_KEY", "")
        else:
            raise Exception("Can't initialize tmdb, please provider a (proper) TMDB_API_KEY!")

        self.naming_convention_map = {
            0: re.compile(r"^(?P<year>\d{4})\s{1}(?P<title>.+)$"),
            1: re.compile(r"^(?P<year>\d{4})\s{1}\-\s{1}(?P<title>.+)$"),
        }
        if naming_convention not in self.naming_convention_map.keys():
            raise Exception("Please provide a proper NAMING_CONVENTION!")
        self.naming_convention = naming_convention

        self.include_adult = include_adult
        self.language = language
        self.backup_call = backup_call

        internal_dfs = []
        for df in [
            "belongs_to_collection",
            "canon_input",
            "cast",
            "crew",
            "genres",
            "movie_details",
            "production_companies",
            "production_countries",
            "spoken_languages",
        ]:
            tmp_df = pd.DataFrame(columns=[k for k in self._get_schema(df).keys()])
            internal_dfs.append(tmp_df)
        (
            self.belongs_to_collection,
            self.canon_input,
            self.cast,
            self.crew,
            self.genres,
            self.movie_details,
            self.production_companies,
            self.production_countries,
            self.spoken_languages,
        ) = internal_dfs

    def _init_client_session(self) -> RetryClient:
        """Sets up a ClientSession with 100 sockets and exponential retry.

        Returns:
          RetryClient
        """
        session_timeout = aiohttp.ClientTimeout(total=None, sock_connect=100, sock_read=100)
        client_session = aiohttp.ClientSession(timeout=session_timeout)
        retry_options = ExponentialRetry(attempts=10)
        return RetryClient(client_session=client_session, retry_options=retry_options)

    async def _request_id(self, retry_client: RetryClient, title: str, year: int) -> pd.DataFrame:
        """Issues an asynchronous request for TMDB ID using movie title and year.

        If the response is malformed or the query yields no results, a TMDB ID of -1 will be returned.

        Args:
          retry_client: RetryClient
          title: movie title
          year: movie release year

        Returns:
          dataframe with columns tmdb_id, request url
        """
        params: Dict[str, object] = {}
        if year == -1:
            params = {"query": title}
        else:
            params = {"query": title, "year": year}

        async with retry_client.get(
            f"https://api.themoviedb.org/3/search/movie?api_key={self.tmdb_api_key}&language={self.language}&page=1&include_adult={self.include_adult}",
            params=params,
            ssl=False,
            allow_redirects=False,
        ) as response:
            if response.status == 200:
                try:
                    resp = await response.json()
                    tmdb_id = resp["results"][0]["id"]
                except IndexError:
                    tmdb_id = -1
            else:
                tmdb_id = -1
        return pd.DataFrame({"tmdb_id": [tmdb_id], "url": [str(response.url)]})

    async def _request_details(self, retry_client: RetryClient, tmdb_id: int) -> None:
        """Issues an asynchronous request for movie details using TMDB ID.

        Args:
          retry_client: RetryClient
          tmdb_id: TMDB ID
        """
        async with retry_client.get(
            f"https://api.themoviedb.org/3/movie/{tmdb_id}?api_key={self.tmdb_api_key}&language={self.language}",
            ssl=False,
            allow_redirects=False,
        ) as response:
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

                spoken_languages = pd.json_normalize(resp["spoken_languages"]).add_prefix("spoken_languages.")
                spoken_languages["tmdb_id"] = tmdb_id
                resp["spoken_languages"] = None
                self.spoken_languages = pd.concat([self.spoken_languages, spoken_languages], ignore_index=True)

                resp["tmdb_id"] = resp.pop("id", None)

                movie_details = pd.json_normalize(resp)
                self.movie_details = self.movie_details.astype({"adult": bool, "video": bool}, errors="ignore")
                self.movie_details = pd.concat([self.movie_details, movie_details], ignore_index=True)

    async def _request_credits(self, retry_client: RetryClient, tmdb_id: int) -> None:
        """Issues an asynchronous request for movie credits using TMDB ID.

        Args:
        retry_client: RetryClient
        tmdb_id: TMDB ID
        """
        async with retry_client.get(
            f"https://api.themoviedb.org/3/movie/{tmdb_id}/credits?api_key={self.tmdb_api_key}&language={self.language}",
            ssl=False,
            allow_redirects=False,
        ) as response:
            if response.status == 200:
                resp = await response.json()
                tmdb_id = resp["id"]

                cast = pd.json_normalize(resp["cast"]).add_prefix("cast.")
                cast["tmdb_id"] = tmdb_id
                resp["cast"] = None
                self.cast["cast.adult"] = self.cast["cast.adult"].astype(bool, errors="ignore")
                self.cast = pd.concat([self.cast, cast], ignore_index=True)

                crew = pd.json_normalize(resp["crew"]).add_prefix("crew.")
                crew["tmdb_id"] = tmdb_id
                resp["crew"] = None
                self.crew["crew.adult"] = self.crew["crew.adult"].astype(bool, errors="ignore")
                self.crew = pd.concat([self.crew, crew], ignore_index=True)

    async def search_ids(self, canon_input: pd.DataFrame) -> pd.DataFrame:
        """Given a canonical input TMDB IDs are searched.

        Args:
          canon_input: dataframe with title and year column

        Returns:
          dataframe with columns tmdb_id, request url
        """
        results = pd.DataFrame(columns=["tmdb_id", "url"])

        if canon_input.empty or {"title", "year"}.issubset(canon_input.columns) is False:
            return results

        async with self._init_client_session() as retry_client:
            tasks = []
            for title, year in zip(canon_input["title"], canon_input["year"], strict=True):
                tasks.append(self._request_id(retry_client, title, year))

            responses = [
                await f
                for f in tqdm.tqdm(
                    asyncio.as_completed(tasks), total=len(tasks), desc="{:<25}".format("recieving tmdb_ids:")
                )
            ]
            for response in responses:
                results = pd.concat([results, response])

        return results.reset_index(drop=True)

    async def get_metadata(self, metadata: str, tmdb_ids: Set[int]) -> None:
        """For a given set of TMDB IDs movie details or credits are searched and stored.

        Args:
          metadata: either 'movie_details' or 'credits'
          tmdb_ids: a set of TMDB IDs

        Raises:
          KeyError: if metadata is not specified correctly
        """
        if metadata not in ["movie_details", "credits"]:
            raise KeyError("metadata should be one of 'movie_details' or 'credits'")

        tmdb_ids = {t for t in tmdb_ids if t >= 0}

        async with self._init_client_session() as retry_client:
            tasks = []
            for tmdb_id in tmdb_ids:
                if metadata == "movie_details":
                    tasks.append(self._request_details(retry_client, tmdb_id))
                else:
                    tasks.append(self._request_credits(retry_client, tmdb_id))

            [
                await f
                for f in tqdm.tqdm(
                    asyncio.as_completed(tasks), total=len(tasks), desc="{:<25}".format(f"recieving {metadata}:")
                )
            ]

    def write(self, output_path: Path) -> None:
        """Writes all internal tables to output_path.

        Args:
          output_path: path where files should get written to.

        Raises:
          FileNotFoundError: if output_path doesn't exist
        """
        if output_path.exists() is False:
            raise FileNotFoundError("Can't write data as OUTPUT_PATH doesn't exist!")

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

    def _extract_queries(self, queries: List[str]) -> pd.DataFrame:
        """Transform queries into a canonical input dataframe.

        Args:
          queries: list of strings

        Returns:
          dataframe with columns title, year
        """
        tmp_input = pd.DataFrame({"query": queries})
        extract = tmp_input["query"].str.extract(self.naming_convention_map[self.naming_convention])
        extract["year"] = extract["year"].fillna(-1).astype(int)
        canon_input = pd.concat([tmp_input, extract], axis=1)
        return canon_input

    def _match_results_pass(
        self, results: pd.DataFrame, pass_df: pd.DataFrame, canon_input: pd.DataFrame, first_pass: bool
    ) -> pd.DataFrame:
        """Solves the mapping of async requests and the canonical input mapping.

        Takes the query=xxxx&year=xxxx portion of the async lookups, extends the pass df so that it can match those
        parameters and joins it onto the canon_input, which is returned.

        Args:
          results:
          pass_df:
          canon_input:
          first_pass: whether this is the first pass

        Returns:
          df
        """
        results["url_match"] = results["url"].str.extract(r".*(&query=.*)$")
        results["url_match"] = results["url_match"].apply(lambda x: urllib.parse.quote_plus(x))

        if first_pass:
            pass_df["url_match"] = np.where(
                pass_df["year"] != -1,
                "&query=" + pass_df["title"] + "&year=" + pass_df["year"].astype(str),
                "&query=" + pass_df["title"],
            )
        else:
            pass_df["url_match"] = "&query=" + pass_df["title"]
        pass_df["url_match"] = pass_df["url_match"].str.replace(" ", "+").apply(lambda x: urllib.parse.quote_plus(x))

        df = pd.merge(pass_df, results, how="left", left_on="url_match", right_on="url_match")[
            ["title", "year", "tmdb_id"]
        ]

        if first_pass:
            tmdb_id_pass = "tmdb_id_first_pass"  # noqa: S105
        else:
            tmdb_id_pass = "tmdb_id_second_pass"  # noqa: S105

        df = df.rename(columns={"tmdb_id": tmdb_id_pass})
        df[tmdb_id_pass] = df[tmdb_id_pass].fillna(-1).astype(int)

        canon_input = pd.merge(canon_input, df[[tmdb_id_pass]], how="left", left_index=True, right_index=True)
        return canon_input

    def generic_parse(self, queries: List[str]) -> None:
        """For a list of given queries, their TMDB IDs will be searched and used to lookup movie details and cast.

        Args:
          queries: list of strings
        """
        self.canon_input = self._extract_queries(queries)

        first_pass_df = self.canon_input.copy()
        first_pass_df = first_pass_df.dropna(subset=["title"])
        results = asyncio.run(self.search_ids(first_pass_df))
        self.canon_input = self._match_results_pass(results, first_pass_df, self.canon_input, first_pass=True)

        if self.backup_call:
            second_pass = self.canon_input[self.canon_input["tmdb_id_first_pass"] == -1][["year", "title"]].copy()
            second_pass["year"] = -1
            results = asyncio.run(self.search_ids(second_pass))

            self.canon_input = self._match_results_pass(results, first_pass_df, self.canon_input, first_pass=False)
            self.canon_input["tmdb_id"] = np.where(
                self.canon_input["tmdb_id_first_pass"] != -1,
                self.canon_input["tmdb_id_first_pass"],
                self.canon_input["tmdb_id_second_pass"],
            )
        else:
            self.canon_input["tmdb_id_second_pass"] = -1
            self.canon_input["tmdb_id"] = self.canon_input["tmdb_id_first_pass"]

        self.canon_input["tmdb_id"] = self.canon_input["tmdb_id"].fillna(-1).astype(int)

        tmdb_ids = set(self.canon_input["tmdb_id"])
        asyncio.run(self.get_metadata(metadata="movie_details", tmdb_ids=tmdb_ids))
        asyncio.run(self.get_metadata(metadata="credits", tmdb_ids=tmdb_ids))

        self._assign_types()

    def parse_movie_dirs(self, input_path: Path) -> None:
        """For a given input path, subfolders will be used for quering the TMDB for metadata.

        Args:
          queries: list of strings

        Raises:
          FileNotFoundError: if input_path doesn't exist.
        """
        if input_path.exists() is False:
            raise FileNotFoundError("Please provide a valid INPUT_PATH!")
        input_folders = [f.name for f in input_path.iterdir() if f.is_dir()]
        self.generic_parse(input_folders)

    def _assign_types(self) -> None:
        """Converts all columns in all dataframes to their correct type."""
        self.canon_input = self.canon_input.astype(
            self._get_schema("canon_input"),
        )
        self.cast = self.cast.astype(self._get_schema("cast"))
        self.crew = self.crew.astype(self._get_schema("crew"))
        self.belongs_to_collection = self.belongs_to_collection.astype(self._get_schema("belongs_to_collection"))
        self.genres = self.genres.astype(self._get_schema("genres"))
        self.production_companies = self.production_companies.astype(self._get_schema("production_companies"))
        self.production_countries = self.production_countries.astype(self._get_schema("production_countries"))
        self.spoken_languages = self.spoken_languages.astype(self._get_schema("spoken_languages"))
        self.movie_details = self.movie_details.astype(self._get_schema("movie_details"))

    def _get_schema(self, schema: str) -> Dict[str, object]:
        """Returns specified schema as dictionary.

        Args:
          schema: which schema to return

        Returns:
          Dictionary containing column-type mapping.

        Raises:
          KeyError: if specified schema is not a valid schema.
        """
        if schema == "canon_input":
            return {
                "year": int,
                "title": str,
                "tmdb_id_first_pass": int,
                "tmdb_id_second_pass": int,
                "tmdb_id": int,
            }
        elif schema == "cast":
            return {
                "tmdb_id": int,
                "cast.adult": bool,
                "cast.gender": int,
                "cast.id": int,
                "cast.known_for_department": "category",
                "cast.name": str,
                "cast.original_name": str,
                "cast.popularity": float,
                "cast.profile_path": str,
                "cast.cast_id": int,
                "cast.character": str,
                "cast.credit_id": str,
                "cast.order": int,
            }
        elif schema == "crew":
            return {
                "tmdb_id": int,
                "crew.adult": bool,
                "crew.gender": int,
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
        elif schema == "belongs_to_collection":
            return {
                "tmdb_id": int,
                "belongs_to_collection.id": int,
                "belongs_to_collection.name": str,
                "belongs_to_collection.poster_path": str,
                "belongs_to_collection.backdrop_path": str,
            }
        elif schema == "genres":
            return {
                "tmdb_id": int,
                "genres.id": int,
                "genres.name": str,
            }
        elif schema == "production_companies":
            return {
                "tmdb_id": int,
                "production_companies.id": int,
                "production_companies.logo_path": str,
                "production_companies.name": "category",
                "production_companies.origin_country": "category",
            }
        elif schema == "production_countries":
            return {
                "tmdb_id": int,
                "production_countries.iso_3166_1": "category",
                "production_countries.name": str,
            }
        elif schema == "spoken_languages":
            return {
                "tmdb_id": int,
                "spoken_languages.english_name": "category",
                "spoken_languages.iso_639_1": "category",
                "spoken_languages.name": str,
            }
        elif schema == "movie_details":
            return {
                "tmdb_id": int,
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
                "runtime": int,
                "status": "category",
                "tagline": str,
                "title": str,
                "video": bool,
                "vote_average": float,
                "vote_count": int,
            }
        else:
            raise KeyError("Specified SCHEMA is unknown!")
