"""Tests for TMDB Async module."""
import asyncio
from pathlib import Path
from typing import List

import pandas as pd
import pytest

from tmdbasync.main import Tmdb


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
def m() -> Tmdb:
    """Returns a TMDB class."""
    return Tmdb()


def test_search_id(m: Tmdb) -> None:
    """Tests for correct handling of canonical input."""
    canon_input = pd.DataFrame({"title": ["The Matrix"], "year": [1999]})
    assert asyncio.run(m.search_ids(canon_input)) == [603]

    canon_input = pd.DataFrame({"title": ["The Matrix"], "year": [None]})
    assert asyncio.run(m.search_ids(canon_input)) == [603]

    canon_input = pd.DataFrame({"title": [""], "year": [None]})
    assert asyncio.run(m.search_ids(canon_input)) == [-1]

    canon_input = pd.DataFrame({"title": ["   "], "year": [None]})
    assert asyncio.run(m.search_ids(canon_input)) == [-1]


def test_get_movie_details_badtmdbids(m: Tmdb) -> None:
    """TMDB_IDs can only be a positive integer.

    some TMDB_IDs don't exist (0, 1) or are a collection (10).
    """
    bad_tmdb_ids = {-1, 0, 1, 10}
    for i in bad_tmdb_ids:
        (
            belongs_to_collection,
            genres,
            production_companies,
            production_countries,
            spoken_languages,
            movie_details,
        ) = asyncio.run(m.get_movie_details({i}))

        assert belongs_to_collection.empty
        assert genres.empty
        assert production_companies.empty
        assert production_countries.empty
        assert spoken_languages.empty
        assert movie_details.empty


def test_get_movie_details_collection(m: Tmdb) -> None:
    """Tests if movie_details are returned for a given TMDB ID.

    603 belongs to collection.
    """
    (
        belongs_to_collection,
        genres,
        production_companies,
        production_countries,
        spoken_languages,
        movie_details,
    ) = asyncio.run(m.get_movie_details({603}))
    assert belongs_to_collection.empty is False
    assert genres.empty is False
    assert production_companies.empty is False
    assert production_countries.empty is False
    assert spoken_languages.empty is False
    assert movie_details.empty is False

    assert m.belongs_to_collection.empty is False
    assert m.genres.empty is False
    assert m.production_companies.empty is False
    assert m.production_countries.empty is False
    assert m.spoken_languages.empty is False
    assert m.movie_details.empty is False


def test_get_movie_details_no_collection(m: Tmdb) -> None:
    """Same as test_get_movie_details_collection, but for a TMDB ID that doesn't belong to a collection."""
    (
        belongs_to_collection,
        genres,
        production_companies,
        production_countries,
        spoken_languages,
        movie_details,
    ) = asyncio.run(m.get_movie_details({2}))
    assert belongs_to_collection.empty is True
    assert genres.empty is False
    assert production_companies.empty is False
    assert production_countries.empty is False
    assert spoken_languages.empty is False
    assert movie_details.empty is False


def test_get_credits_badtmdbids(m: Tmdb) -> None:
    """Tests if credits are empty when searching with invalid TMDB IDs."""
    bad_tmdb_ids = {-1, 0, 1, 10}
    for i in bad_tmdb_ids:
        cast, crew = asyncio.run(m.get_movie_credits({i}))
        assert cast.empty
        assert crew.empty


def test_get_credits_valid(m: Tmdb) -> None:
    """Tests if credits are not empty when searching with valid TMDB IDs."""
    cast, crew = asyncio.run(m.get_movie_credits({604}))
    assert cast.empty is False
    assert crew.empty is False
    assert m.cast.empty is False
    assert m.crew.empty is False


def test_initialization_valid() -> None:
    """Tests if all internal attributes are set correctly after initialization."""
    m = Tmdb(
        tmdb_api_key="abcdefghabcdefghabcdefghabcdefgh",
        include_adult=False,
        language="te_ST",
        naming_convention=1,
        backup_call=False,
    )
    assert m.tmdb_api_key == "abcdefghabcdefghabcdefghabcdefgh"
    assert m.include_adult is False
    assert m.language == "te_ST"
    assert m.backup_call is False
    # TODO check for compiled regex pattern
    # assert m.naming_convention == 1

    assert m.canon_input.empty

    assert m.belongs_to_collection.empty
    assert m.cast.empty
    assert m.crew.empty
    assert m.genres.empty
    assert m.movie_details.empty
    assert m.production_companies.empty
    assert m.production_countries.empty
    assert m.spoken_languages.empty


def test_initialization_invalid(monkeypatch: pytest.MonkeyPatch) -> None:
    """Tests if errors are raised init parameters are invalid."""
    with pytest.raises(Exception) as exc_info:
        Tmdb(tmdb_api_key="abcdefghabcdefghabcdefghabcdefgh", naming_convention=-1)
    assert str(exc_info.value) == "Please provide a proper NAMING_CONVENTION!"

    monkeypatch.delenv("TMDB_API_KEY")
    with pytest.raises(Exception) as exc_info:
        Tmdb()
    assert (
        str(exc_info.value)
        == "Can't initialize tmdb, please provider a (proper) TMDB_API_KEY!"
    )


def test_write(
    m: Tmdb, _input_dir: Path, _output_dir: Path, _sample_movies: List[str]
) -> None:
    """Tests if all internal dataframes are written to output_dir."""
    m.generic_parse(_sample_movies)
    m.write(_output_dir)
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
        m.write(Path("non-existing-output-dir"))
    assert str(exc_info.value) == "Can't write data as OUTPUT_PATH doesn't exist!"


def test_generic_parse_backup(m: Tmdb, _sample_movies: List[str]) -> None:
    """Tests if generic_parse succeeds and writes results into internal dataframes."""
    m.generic_parse(_sample_movies)
    assert m.canon_input.empty is False
    assert m.belongs_to_collection.empty is False
    assert m.cast.empty is False
    assert m.crew.empty is False
    assert m.genres.empty is False
    assert m.movie_details.empty is False
    assert m.production_companies.empty is False
    assert m.production_countries.empty is False
    assert m.spoken_languages.empty is False


def test_generic_parse_nobackup(m: Tmdb, _sample_movies: List[str]) -> None:
    """Sames as test_generic_parse_backup, but instead backup_call is set to false."""
    m.backup_call = False
    m.generic_parse(_sample_movies)
    assert m.canon_input.empty is False
    assert m.belongs_to_collection.empty is False
    assert m.cast.empty is False
    assert m.crew.empty is False
    assert m.genres.empty is False
    assert m.movie_details.empty is False
    assert m.production_companies.empty is False
    assert m.production_countries.empty is False
    assert m.spoken_languages.empty is False


def test_generic_parse_invalid(
    m: Tmdb, _input_dir: Path, _sample_movies: List[str]
) -> None:
    """Tests generic parse with invalid input that has the right format."""
    # bad input
    m.generic_parse(["0000 some-non-existing-movie-title"])
    assert m.canon_input.empty is False
    assert m.belongs_to_collection.empty
    assert m.cast.empty
    assert m.crew.empty
    assert m.genres.empty
    assert m.movie_details.empty
    assert m.production_companies.empty
    assert m.production_countries.empty
    assert m.spoken_languages.empty


def test_parse_movie_dirs(m: Tmdb, _input_dir: Path, _output_dir: Path) -> None:
    """Tests parse_movie_dirs for correct canonical input and parsing."""
    m.parse_movie_dirs(_input_dir)
    assert set(m.canon_input["year"]) == {1999, 2003}
    assert set(m.canon_input["title"]) == {
        "The Matrix",
        "The Matrix Reloaded",
        "The Matrix Revolutions",
    }

    # bad output path
    with pytest.raises(Exception) as exc_info:
        m.parse_movie_dirs(Path("non-existing-output-dir"))
    assert str(exc_info.value) == "Please provide a valid INPUT_PATH!"
