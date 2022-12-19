"""Test cases for the __main__ module."""
import os
from pathlib import Path

import pytest
from click.testing import CliRunner

from movieparse.cli import cli


@pytest.fixture
def runner() -> CliRunner:
    """Fixture for invoking command-line interfaces."""
    return CliRunner()


@pytest.fixture
def root_movie_dir(tmp_path: Path) -> Path:
    """Creates root_movie_dir.

    Args:
      tmp_path: temporary path provided by pytest
    Returns:
      root_movie_dir as path
    """
    rmd = tmp_path / "root_movie_dir"
    rmd.mkdir()
    return rmd


@pytest.fixture
def single_movie(root_movie_dir: Path) -> Path:
    """Creates a single movie folder inside the root_movie_dir.

    Args:
      root_movie_dir: root_movie_dir fixture
    Returns:
      single movie folder as path
    """
    tmp = root_movie_dir / "1999 Fight Club"
    tmp.mkdir()
    return tmp


@pytest.fixture
def output_dir(tmp_path: Path) -> Path:
    """Creates output_dir.

    Args:
      tmp_path: temporary path provided by pytest
    Returns:
      output_dir as path
    """
    output_dir = tmp_path / "output_dir"
    output_dir.mkdir()
    return output_dir


def test_cli_dir(
    runner: CliRunner, output_dir: Path, root_movie_dir: Path, single_movie: Path
) -> None:
    """It exits with a status code of zero."""
    tmdb_api_key = os.getenv("TMDB_API_KEY")
    result = runner.invoke(
        cli,
        [
            "-o",
            str(output_dir),
            "-t",
            tmdb_api_key,
            "-lx",
            "-l",
            "en_US",
            "dir",
            str(root_movie_dir),
        ],
    )

    assert result.exit_code == 0
    flist = [
        "cast",
        # "collections",
        "crew",
        "details",
        "genres",
        "production_companies",
        "production_countries",
        "spoken_languages",
        "mapping",
    ]

    for file in flist:
        assert (output_dir / f"{file}.csv").exists()


def test_cli_list(runner: CliRunner, output_dir: Path) -> None:
    """It exits with a status code of zero."""
    tmdb_api_key = os.getenv("TMDB_API_KEY")
    result = runner.invoke(
        cli,
        [
            "-o",
            str(output_dir),
            "-t",
            tmdb_api_key,
            "-lx",
            "-l",
            "en_US",
            "list",
            "1999 The Matrix",
        ],
    )

    assert result.exit_code == 0
    flist = [
        "cast",
        # "collections",
        "crew",
        "details",
        "genres",
        "production_companies",
        "production_countries",
        "spoken_languages",
        "mapping",
    ]

    for file in flist:
        assert (output_dir / f"{file}.csv").exists()
