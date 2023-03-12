"""Tests for TMDB Async module."""
import asyncio
from pathlib import Path
from typing import List
from typing import Set

import pandas as pd
import pytest

from tmdbasyncmovies.main import TmdbAsyncMovies


@pytest.fixture
def _sample_movies() -> List[str]:
    """Returns a list of sample movies."""
    return [
        "1999 The Matrix",
        "2003 The Matrix Reloaded",
        "2003 The Matrix Revolutions",
    ]


@pytest.fixture
def _input_dir(tmp_path: Path, _sample_movies: List[str]) -> Path:
    """Returns and creates a temporary input_dir with sample movie folders."""
    input_dir = tmp_path / "input_dir"
    input_dir.mkdir()

    for i in _sample_movies:
        tmp = input_dir / i
        tmp.mkdir()
    return input_dir


@pytest.fixture
def _output_dir(tmp_path: Path) -> Path:
    """Returns and creates a temporary output_dir."""
    output_dir = tmp_path / "output_dir"
    output_dir.mkdir()
    return output_dir


@pytest.fixture
def t() -> TmdbAsyncMovies:
    """Returns a TMDB class."""
    return TmdbAsyncMovies()


@pytest.mark.parametrize(
    "tt,canon_input,expected_id",
    [
        (TmdbAsyncMovies(), pd.DataFrame({"title": ["The Matrix"], "year": [1999]}), 603),
        (TmdbAsyncMovies(), pd.DataFrame({"title": ["The Matrix"], "year": [-1]}), 603),
        (TmdbAsyncMovies(), pd.DataFrame({"title": [""], "year": [-1]}), -1),
        (TmdbAsyncMovies(), pd.DataFrame({"title": [" "], "year": [-1]}), -1),
        (TmdbAsyncMovies(), pd.DataFrame(), -1),  # missing title and year columns
        (
            TmdbAsyncMovies(),
            pd.DataFrame(columns=["title", "year"]),
            -1,
        ),  # has no records
    ],
)
def test_search_ids(tt: TmdbAsyncMovies, canon_input: pd.DataFrame, expected_id: int) -> None:
    """Tests for correct handling of canonical input."""
    if canon_input.empty is False:
        result = asyncio.run(tt.search_ids(canon_input))
        assert set(result["tmdb_id"]) == {expected_id}
    else:
        result = asyncio.run(tt.search_ids(canon_input))
        assert result.empty


@pytest.mark.parametrize(
    "tt,tmdb_id_set,empty_metadata,empty_collection",
    [
        (TmdbAsyncMovies(), {-1}, True, True),  # TMDB ID can't be negative
        (TmdbAsyncMovies(), {0}, True, True),  # TMDB ID doesn't exist
        (TmdbAsyncMovies(), {2}, False, True),  # features no collection
        (TmdbAsyncMovies(), {603}, False, False),  # features collection
        (TmdbAsyncMovies(), {}, True, True),  # empty input
    ],
)
def test_get_movie_details(
    tt: TmdbAsyncMovies, tmdb_id_set: Set[int], empty_metadata: bool, empty_collection: bool
) -> None:
    """Tests if requests for TMDB IDs are handled correctly and if metadata is set correctly."""
    (
        belongs_to_collection,
        genres,
        production_companies,
        production_countries,
        spoken_languages,
        movie_details,
    ) = asyncio.run(tt.get_movie_details(tmdb_id_set))

    assert belongs_to_collection.empty is empty_collection
    assert genres.empty is empty_metadata
    assert movie_details.empty is empty_metadata
    assert production_companies.empty is empty_metadata
    assert production_countries.empty is empty_metadata
    assert spoken_languages.empty is empty_metadata

    assert tt.belongs_to_collection.empty is empty_collection
    assert tt.genres.empty is empty_metadata
    assert tt.movie_details.empty is empty_metadata
    assert tt.production_companies.empty is empty_metadata
    assert tt.production_countries.empty is empty_metadata
    assert tt.spoken_languages.empty is empty_metadata


@pytest.mark.parametrize(
    "tt,tmdb_id_set,empty_cast,empty_crew",
    [
        (TmdbAsyncMovies(), {-1}, True, True),  # TMDB ID can't be negative
        (TmdbAsyncMovies(), {0}, True, True),  # TMDB ID doesn't exist
        (TmdbAsyncMovies(), {603}, False, False),  # valid TMDB ID
        (TmdbAsyncMovies(), {}, True, True),  # empty input
    ],
)
def test_get_credits(tt: TmdbAsyncMovies, tmdb_id_set: Set[int], empty_cast: bool, empty_crew: bool) -> None:
    """Tests if requests for movie_details are handled correctly and if metadata is set correctly."""
    cast, crew = asyncio.run(tt.get_movie_credits(tmdb_id_set))
    assert cast.empty is empty_cast
    assert crew.empty is empty_crew
    assert tt.cast.empty is empty_cast
    assert tt.crew.empty is empty_crew


@pytest.mark.parametrize(
    "tmdb_api_key,include_adult,language,naming_convention,backup_call,case",
    [
        ("bad-api-key---------------------", False, "te_ST", 0, False, "valid"),
        ("bad-api-key---------------------", False, "te_ST", -1, False, "bad_naming_convention"),
        (None, False, "te_ST", 0, False, "missing_tmdb_api_key"),
    ],
)
def test_initialization(
    tmdb_api_key: str | None,
    include_adult: bool,
    language: str,
    naming_convention: int,
    backup_call: bool,
    case: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Tests if all internal attributes are set correctly after initialization."""
    if case == "valid":
        t = TmdbAsyncMovies(
            tmdb_api_key=tmdb_api_key,
            include_adult=include_adult,
            language=language,
            naming_convention=naming_convention,
            backup_call=backup_call,
        )
        assert t.tmdb_api_key == tmdb_api_key
        assert t.include_adult is include_adult
        assert t.language == language
        assert t.naming_convention == t.naming_convention_map[naming_convention]
        assert t.backup_call is backup_call

        assert t.canon_input.empty
        assert t.belongs_to_collection.empty
        assert t.cast.empty
        assert t.crew.empty
        assert t.genres.empty
        assert t.movie_details.empty
        assert t.production_companies.empty
        assert t.production_countries.empty
        assert t.spoken_languages.empty
    elif case == "bad_naming_convention":
        with pytest.raises(Exception) as exc_info:
            TmdbAsyncMovies(naming_convention=naming_convention)
        assert str(exc_info.value) == "Please provide a proper NAMING_CONVENTION!"
    else:
        monkeypatch.delenv("TMDB_API_KEY")
        with pytest.raises(Exception) as exc_info:
            TmdbAsyncMovies()
        assert str(exc_info.value) == "Can't initialize tmdb, please provider a (proper) TMDB_API_KEY!"


def test_write(t: TmdbAsyncMovies, _input_dir: Path, _output_dir: Path, _sample_movies: List[str]) -> None:
    """Tests if all internal dataframes are written to output_dir."""
    t.generic_parse(_sample_movies)
    t.write(_output_dir)
    files = [
        "belongs_to_collection.csv",
        "cast.csv",
        "crew.csv",
        "genres.csv",
        "spoken_languages.csv",
        "production_companies.csv",
        "production_companies.csv",
        "movie_details.csv",
    ]
    for f in files:
        assert (_output_dir / f).exists()

    # bad output path
    with pytest.raises(Exception) as exc_info:
        t.write(Path("non-existing-output-dir"))
    assert str(exc_info.value) == "Can't write data as OUTPUT_PATH doesn't exist!"


@pytest.mark.parametrize(
    "t,queries,empty_metadata",
    [
        (TmdbAsyncMovies(), ["1999 The Matrix", "2003 The Matrix Reloaded", "2003 The Matrix Revolutions"], False),
        (TmdbAsyncMovies(), ["0000 some-non-existing-movie-title"], True),
    ],
)
def test_generic_parse(t: TmdbAsyncMovies, queries: List[str], empty_metadata: bool) -> None:
    """Tests if generic_parse succeeds and writes results into internal dataframes."""
    t.generic_parse(queries)
    assert t.canon_input.empty is False
    assert t.belongs_to_collection.empty is empty_metadata
    assert t.cast.empty is empty_metadata
    assert t.crew.empty is empty_metadata
    assert t.genres.empty is empty_metadata
    assert t.movie_details.empty is empty_metadata
    assert t.production_companies.empty is empty_metadata
    assert t.production_countries.empty is empty_metadata
    assert t.spoken_languages.empty is empty_metadata


def test_parse_movie_dirs(t: TmdbAsyncMovies, _input_dir: Path, _output_dir: Path) -> None:
    """Tests parse_movie_dirs for correct canonical input and parsing."""
    t.parse_movie_dirs(_input_dir)
    assert t.canon_input[t.canon_input["title"] == "The Matrix"]["tmdb_id"].iloc[0] == 603
    assert t.canon_input[t.canon_input["title"] == "The Matrix Reloaded"]["tmdb_id"].iloc[0] == 604
    assert t.canon_input[t.canon_input["title"] == "The Matrix Revolutions"]["tmdb_id"].iloc[0] == 605

    # bad input path
    with pytest.raises(Exception) as exc_info:
        t.parse_movie_dirs(Path("non-existing-output-dir"))
    assert str(exc_info.value) == "Please provide a valid INPUT_PATH!"


def test_get_schema_invalid(t: TmdbAsyncMovies) -> None:
    """Tests for raising error if schema doesn't exist."""
    with pytest.raises(KeyError) as exc_info:
        t._get_schema("invalid-schema")
    assert str(exc_info.value) == "'Specified SCHEMA is unknown!'"


@pytest.mark.parametrize("execution_number", range(10))
def test_async_order(_sample_movies: List[str], execution_number: int):
    """This test adresses the problem that aiohttp requests return unordered."""
    t = TmdbAsyncMovies()
    t.generic_parse(_sample_movies)
    assert t.canon_input[t.canon_input["title"] == "The Matrix"]["tmdb_id"].iloc[0] == 603
    assert t.canon_input[t.canon_input["title"] == "The Matrix Reloaded"]["tmdb_id"].iloc[0] == 604
    assert t.canon_input[t.canon_input["title"] == "The Matrix Revolutions"]["tmdb_id"].iloc[0] == 605
