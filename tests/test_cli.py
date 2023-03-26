"""Tests for tmdbasyncmovies CLI."""

from pathlib import Path
from typing import List

import pandas as pd
import pytest
from click.testing import CliRunner

from tmdb_async_movies.cli import tmdbasyncmovies


@pytest.fixture
def runner() -> CliRunner:
    """Fixture for invoking command-line interfaces."""
    return CliRunner()


@pytest.fixture
def _sample_movies() -> List[str]:
    """Returns a list of sample movies."""
    return [
        "1999 The Matrix",
        "2003 The Matrix Reloaded",
        "2003 The Matrix Revolutions",
    ]


@pytest.fixture
def input_dir(tmp_path: Path, _sample_movies: List[str]) -> Path:
    """Returns and creates a temporary input_dir with sample movie folders."""
    input_dir = tmp_path / "input_dir"
    input_dir.mkdir()

    for i in _sample_movies:
        tmp = input_dir / i
        tmp.mkdir()
    return input_dir


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


def _check_for_success(output_dir: Path) -> None:
    flist = [
        "belongs_to_collection",
        "canon_input",
        "cast",
        "crew",
        "genres",
        "movie_details",
        "production_companies",
        "production_countries",
        "spoken_languages",
    ]

    for file in flist:
        assert (output_dir / f"{file}.csv").exists()

    df = pd.read_csv(output_dir / "canon_input.csv")
    assert set(df["year"]) == {1999, 2003}
    assert set(df["title"]) == {"The Matrix", "The Matrix Reloaded", "The Matrix Revolutions"}


def test_cli_from_dir(runner: CliRunner, input_dir: Path, output_dir: Path) -> None:
    """Tests if CLI with from_dir command is successful."""
    result = runner.invoke(
        tmdbasyncmovies,
        ["-o", str(output_dir), "from_dir", str(input_dir)],
    )

    assert result.exit_code == 0
    _check_for_success(output_dir)


def test_cli_from_input(runner: CliRunner, output_dir: Path, _sample_movies: List[str]) -> None:
    """Tests if CLI with from_input command is successful."""
    result = runner.invoke(
        tmdbasyncmovies,
        ["-o", str(output_dir), "from_input", *_sample_movies],
    )

    assert result.exit_code == 0
    _check_for_success(output_dir)
