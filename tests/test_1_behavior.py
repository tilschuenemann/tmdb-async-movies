import os
import pathlib

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
def multiple_movies(root_movie_dir):
    paths = []
    for subdir in ["1999 The Matrix", "2003 The Matrix Reloaded", "2003 The Matrix Revolutions"]:
        tmp = root_movie_dir / subdir
        tmp.mkdir()
        paths.append(tmp)
    return paths


@pytest.fixture
def mapping_stub(output_path, multiple_movies):
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


def test_persist_custom_ids(output_path, mapping_stub):
    m = movieparse(output_path=output_path)
    m.parse_movielist(["1999 Fight Club"])
    assert set(m.mapping["tmdb_id_man"]) == set([0, 777, 888])
    (output_path / "mapping.csv").unlink()


def test_initialization(output_path, monkeypatch):
    # create sample data
    m = movieparse(output_path=output_path)
    m.parse_movielist(["1999 Fight Club"])
    m.write()

    # output dir cant be a file
    f = output_path / "otherfile"
    f.touch()

    with pytest.raises(SystemExit) as pytest_wrapped_e:
        movieparse(f)
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == "please supply an OUTPUT_DIR that is a directory!"

    # parsing_style has to be supported
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        movieparse(parsing_style=999)
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == "please supply a valid PARSING_STYLE!"

    # caches are read correctly
    m = movieparse(output_path=output_path)
    assert m.cached_mapping.empty is False
    assert set(m.cached_mapping_ids) == set([550])
    assert set(m.cached_metadata_ids) == set([550])

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
        movieparse()
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == "please supply a TMDB_API_KEY!"

    # supply api key
    m = movieparse(tmdb_api_key="example-key")
    assert m._movieparse__TMDB_API_KEY == "example-key"


def test_guess_parsing_style():
    # if styles overlap, the first matching style is chosen (zero in this case)
    m = movieparse()
    m.parse_movielist(movielist=["1999 Fight Club", "1999 - Fight Club"])
    assert m._movieparse__PARSING_STYLE == 0

    # parsing style with most matches is chosen
    m = movieparse()
    m.parse_movielist(movielist=["1999 Fight Club", "Fight Club"])
    assert m._movieparse__PARSING_STYLE == 0

    # no matches throws error
    m = movieparse()
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        m.parse_movielist(movielist=["Fight Club"])
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == "couldn't estimate a parsing style, please supply one for yourself!"


def test_get_id():
    pass


def test_caching_behavior():
    pass
    # no cache
    # skip lookup
    # metadata_id cache
    # eager
