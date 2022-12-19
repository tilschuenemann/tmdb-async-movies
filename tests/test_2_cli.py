"""Test cases for the __main__ module."""
import os
from pathlib import Path
from typing import List

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


@pytest.fixture
def args(output_dir: Path) -> List[str]:
    """Fixture with all possible arguments in list."""
    return [
        "-t",
        str(os.getenv("TMDB_API_KEY")),
        "-lx",
        "-l",
        "en_US",
        "-o",
        str(output_dir),
    ]


def test_cli_dir(
    runner: CliRunner,
    output_dir: Path,
    root_movie_dir: Path,
    single_movie: Path,
    args: List[str],
) -> None:
    """It exits with a status code of zero."""
    result = runner.invoke(
        cli,
        [
            *args,
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


def test_cli_list(runner: CliRunner, output_dir: Path, args: List[str]) -> None:
    """It exits with a status code of zero."""
    result = runner.invoke(
        cli,
        [
            *args,
            "list",
            ("1999 The Matrix"),
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
