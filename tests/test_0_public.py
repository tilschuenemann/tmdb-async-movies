import json

import pandas as pd
import pytest

from movieparse.main import movieparse


@pytest.fixture
def output_path(tmp_path):
    output_path = tmp_path / "output_path"
    output_path.mkdir()
    return output_path


@pytest.fixture
def root_movie_dir(tmp_path):
    rmd = tmp_path / "root_movie_dir"
    rmd.mkdir()
    return rmd


@pytest.fixture
def single_movie(root_movie_dir):
    tmp = root_movie_dir / "1999 Fight Club"
    tmp.mkdir()
    return tmp


@pytest.fixture
def single_movie_conv2(root_movie_dir):
    tmp = root_movie_dir / "1999 - Fight Club"
    tmp.mkdir()
    return tmp


@pytest.fixture
def multiple_movies(root_movie_dir):
    paths = []
    for subdir in ["1999 The Matrix", "2003 The Matrix Reloaded", "2003 The Matrix Revolutions"]:
        tmp = root_movie_dir / subdir
        tmp.mkdir()
        paths.append(tmp)
    return paths


def filecount(dir):
    i = 0
    for file in dir.iterdir():
        i += 1
    return i


def test_parse_movielist(output_path):
    # bad input (empty list)
    with pytest.raises(Exception) as exc_info:
        x = movieparse()
        x.parse_movielist([])
    assert str(exc_info.value) == "movielist can't be empty!"

    assert filecount(output_path) == 0
    # valid input
    m = movieparse(output_path=output_path, parsing_style=0)
    mlist = ["1999 Fight Club"]

    m.parse_movielist(mlist)
    m.write()

    assert set(m.mapping["tmdb_id"]) == set([550])
    assert set(m.mapping["tmdb_id_man"]) == set([0])
    assert set(m.mapping["input"]) == set(mlist)
    assert set(m.mapping["canonical_input"]) == set(mlist)

    assert set(m.metadata_lookup_ids) == set([550])

    assert m.cast.empty is False
    # assert m.collect.empty is False
    assert m.crew.empty is False
    assert m.details.empty is False
    assert m.genres.empty is False
    assert m.prod_comp.empty is False
    assert m.prod_count.empty is False
    assert m.spoken_langs.empty is False

    assert m.cached_mapping.empty
    assert set(m.cached_mapping_ids) == set([])
    assert set(m.cached_metadata_ids) == set([])

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


def test_parse_root_movie_dir(output_path, root_movie_dir, single_movie):

    # bad input (file not dir)
    f = output_path / "otherfile"
    f.touch()

    with pytest.raises(Exception) as exc_info:
        x = movieparse()
        x.parse_root_movie_dir(f)
    assert str(exc_info.value) == "root_movie_dir has to a directory!"
    f.unlink()

    # valid input
    assert filecount(output_path) == 0
    m = movieparse(output_path=output_path, parsing_style=0)

    assert m.cached_mapping.empty
    assert set(m.cached_mapping_ids) == set([])
    assert set(m.cached_metadata_ids) == set([])

    m.parse_root_movie_dir(root_movie_dir)
    m.write()

    assert set(m.mapping["tmdb_id"]) == set([550])
    assert set(m.mapping["tmdb_id_man"]) == set([0])
    assert set(m.mapping["input"]) == set([single_movie])
    assert set(m.mapping["canonical_input"]) == set([single_movie.name])

    # assert m.cast.empty is False
    # # assert m.collect.empty is False
    # assert m.crew.empty is False
    # assert m.details.empty is False
    # assert m.genres.empty is False
    # assert m.prod_comp.empty is False
    # assert m.prod_count.empty is False
    # assert m.spoken_langs.empty is False

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


def test_movieparse_public_interface():
    m = movieparse()

    caches = ["cached_mapping", "cached_mapping_ids", "cached_metadata_ids"]
    methods = ["get_parsing_patterns", "parse_movielist", "parse_root_movie_dir", "write"]
    metadata = ["cast", "collect", "crew", "details", "genres", "prod_comp", "prod_count", "spoken_langs"]

    assert set(["mapping", *caches, *methods, *metadata]) == set([x for x in dir(m) if not x.startswith("_")])
