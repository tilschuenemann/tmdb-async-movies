"""yaya.

yaya.

Typical usage example:

foo = ClassFoo()
bar = foo.FunctionBar()
"""

import asyncio
import os
import re
from pathlib import Path
from typing import Dict
from typing import List

import aiohttp
import numpy as np
import pandas as pd
from tqdm import tqdm


class Movieparse:
    """Movieparse object used for storing configuration and metadata.

    Attributes:
      output_dir: Output directory where files get written to.
      tmdb_api_key: TMDB API Key. Falls back to environment variable TMDB_API_KEY.
      parsing_style: Define parsing style to use. -1 for estimating parsing style.
      strict: Always use title and release year for looking up metadata, no fallback to title only.
      language: ISO-639-1 shortcode for getting locale information.
    """

    mapping = pd.DataFrame()
    cast = (
        collect
    ) = crew = details = genres = prod_comp = prod_count = spoken_langs = pd.DataFrame()
    cached_mapping = pd.DataFrame()

    default_codes = {
        "DEFAULT": 0,
        "NO_RESULT": -1,
        "NO_EXTRACT": -2,
        "BAD_RESPONSE": -3,
    }

    @staticmethod
    def get_parsing_patterns() -> dict[int, re.Pattern[str]]:
        """Lists all valid patterns for extracting title and (optionally release year) from input.

        Returns:
          A dict mapping integer keys to their regex pattern.
        """
        return {
            0: re.compile(r"^(?P<disk_year>\d{4})\s{1}(?P<disk_title>.+)$"),
            1: re.compile(r"^(?P<disk_year>\d{4})\s-\s(?P<disk_title>.+)$"),
            2: re.compile(r"^(?P<disk_title>.+)\s(?P<disk_year>\d{4})$"),
        }

    def __init__(
        self,
        output_dir: Path | None = None,
        tmdb_api_key: str | None = None,
        parsing_style: int = -1,
        strict: bool = False,
        language: str = "en_US",
    ):
        """Initilizes movieparser."""
        self._STRICT = strict
        self._LANGUAGE = language

        if output_dir is None:
            output_dir = Path.cwd()
        elif output_dir.is_dir() is False:
            raise Exception("please supply an OUTPUT_DIR that is a directory!")
        self._OUTPUT_DIR = output_dir

        if tmdb_api_key is None and os.getenv("TMDB_API_KEY") is not None:
            self._TMDB_API_KEY = os.getenv("TMDB_API_KEY")
        elif tmdb_api_key is not None:
            self._TMDB_API_KEY = tmdb_api_key
        else:
            raise Exception("please supply a TMDB_API_KEY!")

        if parsing_style not in range(
            -1, max(Movieparse.get_parsing_patterns().keys())
        ):
            raise Exception("please supply a valid PARSING_STYLE!")
        else:
            self._PARSING_STYLE = parsing_style

        self._read_existing()

    def _metadata(self) -> dict[str, pd.DataFrame]:
        """Provides a dictionary for compactly allocating metadata.

        Returns:
          Dictionary with filenames as keys and internal dataframes as values.
        """
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

    def _read_existing(self) -> None:
        """Uses _table_iter() to read existing metadata and append to internal dataframes."""
        df_list = []
        for fname, df in self._metadata().items():
            tmp_path = self._OUTPUT_DIR / f"{fname}.csv"
            if tmp_path.exists():
                df = pd.read_csv(tmp_path)
                df = self._assign_types(df)
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

        tmp_path = self._OUTPUT_DIR / "mapping.csv"
        if tmp_path.exists():
            self.cached_mapping = pd.read_csv(tmp_path)
            self.cached_mapping = self._assign_types(self.cached_mapping)

    def parse_movielist(self, movielist: List[str]) -> None:
        """Parse movie metadata from movielist.

        Args:
          movielist: List of titles (and optionally release years).
        """
        if not movielist:
            raise Exception("movielist can't be empty!")

        self.mapping = pd.DataFrame(
            {
                "input": movielist,
                "canonical_input": movielist,
            }
        )

        self._generic_parse()

    def parse_root_movie_dir(self, root_movie_dir: Path) -> None:
        """Parse movie metadata from folders inside root_movie_dir.

        Args:
          root_movie_dir: directory where movie subfolders lie.
        """
        if root_movie_dir.is_dir() is False:
            raise Exception("root_movie_dir has to be a directory!")

        names = []
        for folder in root_movie_dir.iterdir():
            if folder.is_dir():
                names.append(folder)

        self.mapping = pd.DataFrame(
            {
                "input": names,
                "canonical_input": [x.name for x in names],
            }
        )

        self._generic_parse()

    def _generic_parse(self) -> None:
        self.mapping["tmdb_id"] = self.default_codes["NO_EXTRACT"]
        self.mapping["tmdb_id_man"] = self.default_codes["DEFAULT"]

        if self._PARSING_STYLE == -1:
            self._guess_parsing_style()

        self._update_mapping()
        self._get_ids()
        self._update_metadata_lookup_ids()
        asyncio.run(self._get_metadata())

    def _guess_parsing_style(self) -> None:
        """Iterates over canonical input, matching the _PARSING_STYLE  according to most matches.

        Raises:
          Expection if two or more styles have the same amount of matches or if no styles match.
        """
        tmp = self.mapping[["canonical_input"]].copy()
        max_matches = 0
        conflict = False
        for style, pattern in Movieparse.get_parsing_patterns().items():
            matches = (
                tmp["canonical_input"]
                .str.extract(pattern, expand=True)
                .notnull()
                .sum()
                .sum()
            )
            if matches > max_matches:
                self._PARSING_STYLE = style
                max_matches = matches
                conflict = False
            elif matches == max_matches:
                conflict = True

        if max_matches == 0 and self._PARSING_STYLE == -1 or conflict:
            raise Exception(
                "couldn't estimate a parsing style, please supply one for yourself!"
            )

        accuracy = f"{(max_matches / (len(tmp.index) * 2) * 100):.2f}"
        print(f"best parsing style: {self._PARSING_STYLE} with {accuracy}% accuracy")

    def _update_mapping(self) -> None:
        """Concatenates cached mapping and newly generated mapping, keeping the cached mappings entries if duplicates occur.

        For dupes only the column canonical_input is considered. If the user previously entered values in tmdb_id_man,
        these will be kept.
        """
        self.mapping = pd.concat(
            [self.cached_mapping, self.mapping], axis=0, ignore_index=True
        ).drop_duplicates(subset="canonical_input", keep="first")

    def _get_ids(self) -> None:
        asyncio.run(self._get_ids_async(exact=True))

        if not self._STRICT:
            asyncio.run(self._get_ids_async(exact=False))

        self.mapping = self._assign_types(self.mapping)
        self.mapping.to_csv(
            (self._OUTPUT_DIR / "mapping.csv"), date_format="%Y-%m-%d", index=False
        )

    async def _get_ids_async(self, exact: bool) -> None:
        """Asynchronously lookup tmdb_ids from canonical_input.

        Args:
          exact: whether to create tasks using title and year only.

        Returns:
          dataframe with a potentially incomplete index and column tmdb_id.

        Uses _PARSING_STYLE to extract title and year from canonical input. If input doesn't match it's dropped from canon_ext.
        This missing index is used later for stitching the results together.
        Depending on the exact-argument a list of tasks is created and then run asynchronously.
        """
        pattern = Movieparse.get_parsing_patterns()[self._PARSING_STYLE]
        needed_lookups = self.mapping[
            self.mapping["tmdb_id"].isin([v for v in self.default_codes.values()])
        ].copy()
        canon_ext = (
            needed_lookups["canonical_input"]
            .str.extract(pattern, expand=True)
            .dropna(how="any", axis=0)
        )

        session = aiohttp.ClientSession()
        if exact:
            tasks = [
                session.get(
                    f"https://api.themoviedb.org/3/search/movie/?api_key={self._TMDB_API_KEY}&query={x}&year={y}&include_adult=true",
                    ssl=False,
                )
                for x, y in zip(canon_ext["disk_title"], canon_ext["disk_year"])
            ]
        else:
            tasks = [
                session.get(
                    f"https://api.themoviedb.org/3/search/movie/?api_key={self._TMDB_API_KEY}&query={x}&include_adult=true",
                    ssl=False,
                )
                for x in canon_ext["disk_title"]
            ]

        results = []
        responses = [
            await f
            for f in tqdm(
                asyncio.as_completed(tasks),
                desc="{:<35}".format(f"getting ids from TMDB, exact: {exact}"),
                total=len(tasks),
            )
        ]
        for response in responses:
            try:
                resp = await response.json()
                results.append(resp["results"][0]["id"])
            except IndexError:
                results.append(self.default_codes["NO_RESULT"])
            except KeyError:
                results.append(self.default_codes["BAD_RESPONSE"])
        await session.close()

        tmp = pd.DataFrame({"tmdb_id": results}, index=canon_ext.index).reindex(
            self.mapping.index
        )

        self.mapping["tmdb_id"] = np.where(
            pd.notnull(tmp["tmdb_id"]), tmp["tmdb_id"], self.mapping["tmdb_id"]
        )

    def _update_metadata_lookup_ids(self) -> None:
        """Creates a set of ids for looking up metadata and removes movieparse default_codes."""
        self.metadata_lookup_ids = set(self.mapping["tmdb_id"]) | set(
            self.mapping["tmdb_id_man"]
        )

        self.metadata_lookup_ids -= {x for x in self.default_codes.values()}

    def _dissect_metadata_response(self, response: Dict[str, object]) -> None:
        results = []
        tmdb_id = response.pop("id")
        for c, df in self._metadata().items():

            tmp = pd.DataFrame()

            if c in ["cast", "crew"]:
                tmp = pd.json_normalize(response["credits"].pop(c)).add_prefix(f"{c}.")  # type: ignore [attr-defined]
            elif c == "collection":
                collect = response.pop("belongs_to_collection")
                if collect is not None:
                    tmp = pd.json_normalize(collect).add_prefix(f"{c}.")
            elif c == "details":
                tmp = pd.json_normalize(response)
            else:
                tmp = pd.json_normalize(response.pop(c)).add_prefix(f"{c}.")

            tmp["tmdb_id"] = tmdb_id

            if tmp.empty is False:
                first_column = tmp.pop("tmdb_id")
                tmp.insert(0, "tmdb_id", first_column)

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

    async def _get_metadata(self) -> None:
        session = aiohttp.ClientSession()
        tasks = [
            session.get(
                f"https://api.themoviedb.org/3/movie/{tmdb_id}?api_key={self._TMDB_API_KEY}&language={self._LANGUAGE}&append_to_response=credits",
                ssl=False,
            )
            for tmdb_id in self.metadata_lookup_ids
        ]

        responses = [
            await f
            for f in tqdm(
                asyncio.as_completed(tasks),
                desc="{:<35}".format("getting metadata from TMDB"),
                total=len(tasks),
            )
        ]
        for response in tqdm(responses, desc="{:<35}".format("organizing responses")):
            if response.status == 200:
                self._dissect_metadata_response(await response.json())
        await session.close()

    def write(self) -> None:
        """Writes all non-empty metadata dataframes as CSV files to output_dir."""
        for fname, df in self._metadata().items():
            tmp_path = self._OUTPUT_DIR / f"{fname}.csv"
            if df.empty is False:
                df.to_csv(
                    tmp_path, date_format="%Y-%m-%d", index=False, float_format="%.3f"
                )

    def _assign_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """Casts df columns to specified types.

        tmdb_id is shared among all metadata files but only listed for mapping.csv.

        Args:
          df: dataframe to be casted
        Returns:
          df with casted columns.
        """
        types = {
            # mapping.csv
            "tmdb_id": "int32",
            "tmdb_id_man": "int32",
            "input": object,  # can be both a string and a path!
            "canonical_input": str,
            # cast.csv
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
            # collections.csv
            "collection.id": int,
            "collection.name": str,
            "collection.poster_path": str,
            "collection.backdrop_path": str,
            # crew.csv
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
            # genres.csv
            "genres.id": "int8",
            "genres.name": str,
            # production_companies.csv
            "production_companies.id": "int32",
            "production_companies.logo_path": str,
            "production_companies.name": "category",
            "production_companies.origin_country": "category",
            "production_countries.iso_3166_1": "category",
            "production_countries.name": str,
            # spoken_languages.csv
            "spoken_languages.english_name": "category",
            "spoken_languages.iso_3166_1": "category",
            "spoken_languages.name": str,
            # details.csv
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

        for k, v in types.items():
            if k in df.columns:
                df[k] = df[k].astype(v)
        return df
