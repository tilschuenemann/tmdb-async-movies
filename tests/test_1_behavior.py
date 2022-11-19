"""A one line summary of the module or program, terminated by a period.

Leave one blank line.  The rest of this docstring should contain an
overall description of the module or program.  Optionally, it may also
contain a brief description of exported classes and functions and/or usage
examples.

Typical usage example:

foo = ClassFoo()
bar = foo.FunctionBar()
"""

from pathlib import Path
from typing import List

import pandas as pd
import pytest

from movieparse.main import Movieparse


@pytest.fixture
def output_path(tmp_path: Path) -> Path:
    """Creates output_dir.

    Args:
      tmp_path: temporary path provided by pytest
    Returns:
      output_dir as path
    """
    output_path = tmp_path / "output_path"
    output_path.mkdir()
    return output_path


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
def multiple_movies(root_movie_dir: Path) -> List[Path]:
    """Creates a multiple movie folders inside the root_movie_dir.

    Args:
      root_movie_dir: root_movie_dir fixture
    Returns:
      list of paths of movie folders
    """
    paths = []
    for subdir in [
        "1999 The Matrix",
        "2003 The Matrix Reloaded",
        "2003 The Matrix Revolutions",
    ]:
        tmp = root_movie_dir / subdir
        tmp.mkdir()
        paths.append(tmp)
    return paths


@pytest.fixture
def mapping_stub(output_path: Path, multiple_movies: List[Path]) -> pd.DataFrame:
    """Creates a mapping stub."""
    mapping_stub = pd.DataFrame(
        {
            "input": multiple_movies,
            "canonical_input": multiple_movies,
            "tmdb_id": [603, 0, 605],
            "tmdb_id_man": [0, 777, 888],
        }
    )
    mapping_stub.to_csv((output_path / "mapping.csv"), index=False)
    return mapping_stub


def test_persist_custom_ids(output_path: Path, mapping_stub: pd.DataFrame) -> None:
    """Check that mapping custom ids dont get deleted or overwritten.

    Args:
      output_path: output_path fixture
      mapping_stub: mapping_stub fixture
    """
    m = Movieparse(output_path=output_path)
    m.parse_movielist(["1999 Fight Club"])
    assert set(m.mapping["tmdb_id_man"]) == {0, 777, 888}
    (output_path / "mapping.csv").unlink()


def test_initialization(output_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Tests Movieparse object initialization.

    Init behavior should include:
    * output_dir should be a directory
    * parsing style has to be valid
    * caches should be created
    * metadata in output_dir should be read correctly
    * an API key has to be supplied either by env var or manually
    Args:
      output_path: output_path fixture
      monkeypatch: monkeypatch fixture
    """
    # create sample data
    m = Movieparse(output_path=output_path)
    m.parse_movielist(["1999 Fight Club"])
    m.write()

    # output dir cant be a file
    f = output_path / "otherfile"
    f.touch()

    with pytest.raises(SystemExit) as pytest_wrapped_e:
        Movieparse(f)
    assert pytest_wrapped_e.type == SystemExit
    assert (
        pytest_wrapped_e.value.code
        == "please supply an OUTPUT_DIR that is a directory!"
    )

    # parsing_style has to be supported
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        Movieparse(parsing_style=999)
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == "please supply a valid PARSING_STYLE!"

    # caches are read correctly
    m = Movieparse(output_path=output_path)
    assert m.cached_mapping.empty is False
    assert set(m.cached_mapping_ids) == {550}
    assert set(m.cached_metadata_ids) == {550}

    # existing metadata is read correctly
    assert m.cast.empty is False
    # assert m.collect.empty is False
    assert m.crew.empty is False
    assert m.details.empty is False
    assert m.genres.empty is False
    assert m.prod_comp.empty is False
    assert m.prod_count.empty is False
    assert m.spoken_langs.empty is False

    # error if no api key is supplied
    monkeypatch.delenv("TMDB_API_KEY")
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        Movieparse()
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == "please supply a TMDB_API_KEY!"

    # supply api key
    m = Movieparse(tmdb_api_key="example-key")
    # assert m._movieparse__TMDB_API_KEY == "example-key"


def test_guess_parsing_style() -> None:
    """Tests for correct estimation of parsing styles."""
    # if styles overlap, the first matching style is chosen (zero in this case)
    m = Movieparse()
    m.parse_movielist(movielist=["1999 Fight Club", "1999 - Fight Club"])
    # assert m._movieparse__PARSING_STYLE == 0

    # parsing style with most matches is chosen
    m = Movieparse()
    m.parse_movielist(movielist=["1999 Fight Club", "Fight Club"])
    # assert m._movieparse__PARSING_STYLE == 0

    # no matches throws error
    m = Movieparse()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        m.parse_movielist(movielist=["Fight Club"])
    assert pytest_wrapped_e.type == SystemExit
    assert (
        pytest_wrapped_e.value.code
        == "couldn't estimate a parsing style, please supply one for yourself!"
    )