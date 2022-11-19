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
def single_movie_conv2(root_movie_dir: Path) -> Path:
    """Creates a single movie folder inside the root_movie_dir, using another naming convention.

    Args:
      root_movie_dir: root_movie_dir fixture
    Returns:
      single movie folder as path
    """
    tmp = root_movie_dir / "1999 - Fight Club"
    tmp.mkdir()
    return tmp


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


def _filecount(dir: Path) -> int:
    """Counts amount of files in directory.

    Counts amount of files in directory.

    Args:
      dir: parent directory for counting.

    Returns:
      int amount of files
    """
    i = 0
    for _file in dir.iterdir():
        i += 1
    return i


def test_parse_movielist(output_path: Path) -> None:
    """Tests parsing from movielist.

    Tests with invalid input (empty list), expecting an error.
    Tests with valid input, expecting a full mapping and metadata as attribute and csv file.

    Args:
      output_path: output_path fixture
    Returns:
      None
    """
    # bad input (empty list)
    with pytest.raises(Exception) as exc_info:
        x = Movieparse()
        x.parse_movielist([])
    assert str(exc_info.value) == "movielist can't be empty!"
    assert _filecount(output_path) == 0

    # valid input
    m = Movieparse(output_path=output_path, parsing_style=0)
    mlist = ["1999 Fight Club"]

    m.parse_movielist(mlist)
    m.write()

    assert set(m.mapping["tmdb_id"]) == {550}
    assert set(m.mapping["tmdb_id_man"]) == {0}
    assert set(m.mapping["input"]) == set(mlist)
    assert set(m.mapping["canonical_input"]) == set(mlist)

    assert set(m.metadata_lookup_ids) == {550}

    assert m.cast.empty is False
    # assert m.collect.empty is False
    assert m.crew.empty is False
    assert m.details.empty is False
    assert m.genres.empty is False
    assert m.prod_comp.empty is False
    assert m.prod_count.empty is False
    assert m.spoken_langs.empty is False

    assert m.cached_mapping.empty
    assert set(m.cached_mapping_ids) == set()
    assert set(m.cached_metadata_ids) == set()

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
        assert (output_path / f"{file}.csv").exists()


def test_parse_root_movie_dir(
    output_path: Path, root_movie_dir: Path, single_movie: Path
) -> None:
    """Tests parsing from root_movie dir.

    Testing with invalid input, where root_movie_dir is not a directory.
    Testing with valid input, checking for correct mapping and correct metadata in object and csv files.

    Args:
      output_path: output_path fixture
      root_movie_dir: root_movie_dir fixture
      single_movie: single_movie fixture
    """
    # bad input (file not dir)
    f = output_path / "otherfile"
    f.touch()

    with pytest.raises(Exception) as exc_info:
        x = Movieparse()
        x.parse_root_movie_dir(f)
    assert str(exc_info.value) == "root_movie_dir has to a directory!"
    f.unlink()

    # valid input
    assert _filecount(output_path) == 0
    m = Movieparse(output_path=output_path, parsing_style=0)

    assert m.cached_mapping.empty
    assert set(m.cached_mapping_ids) == set()
    assert set(m.cached_metadata_ids) == set()

    m.parse_root_movie_dir(root_movie_dir)
    m.write()

    assert set(m.mapping["tmdb_id"]) == {550}
    assert set(m.mapping["tmdb_id_man"]) == {0}
    assert set(m.mapping["input"]) == {single_movie}
    assert set(m.mapping["canonical_input"]) == {single_movie.name}

    assert m.cast.empty is False
    # assert m.collect.empty is False
    assert m.crew.empty is False
    assert m.details.empty is False
    assert m.genres.empty is False
    assert m.prod_comp.empty is False
    assert m.prod_count.empty is False
    assert m.spoken_langs.empty is False

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
        assert (output_path / f"{file}.csv").exists()


def test_movieparse_public_interface() -> None:
    """Checks for public available interfaces."""
    m = Movieparse()

    caches = ["cached_mapping", "cached_mapping_ids", "cached_metadata_ids"]
    methods = [
        "get_parsing_patterns",
        "parse_movielist",
        "parse_root_movie_dir",
        "write",
    ]
    metadata = [
        "cast",
        "collect",
        "crew",
        "details",
        "genres",
        "prod_comp",
        "prod_count",
        "spoken_langs",
    ]

    assert {"mapping", *caches, *methods, *metadata} == {
        x for x in dir(m) if not x.startswith("_")
    }