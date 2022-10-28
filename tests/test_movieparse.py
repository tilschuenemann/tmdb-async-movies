from movieparse import __version__
import pytest
from movieparse.main import movieparse
import numpy as np
import pandas as pd
import numpy as np

NA_VALUE = 0
MAPPING_COLS = set(["disk_path", "tmdb_id", "tmdb_id_man"])
MAPPING_COL_AMOUNT = 3


@pytest.fixture
def root_movie_dir(tmp_path):
    subdirs = [
        "1999 The Matrix",
        "2003 The Matrix Reloaded",
        "2003 The Matrix Revolutions",
    ]

    rmd = tmp_path / "rmd"
    rmd.mkdir()
    for movie_dir in subdirs:
        tmp = rmd / movie_dir
        tmp.mkdir()
    return rmd


@pytest.fixture
def mapping_outdated_tmdb_id(tmp_path, root_movie_dir, output_path):

    dirs = [
        root_movie_dir / "1999 The Matrix",
        root_movie_dir / "2003 The Matrix Reloaded",
        root_movie_dir / "2003 The Matrix Revolutions",
    ]

    mapping = pd.DataFrame(
        {
            "disk_path": dirs,
            "tmdb_id": [1, 604, 605],
            "tmdb_id_man": [NA_VALUE, NA_VALUE, NA_VALUE],
        }
    )

    mapping.to_csv(output_path / "mapping.csv", index=False)


@pytest.fixture
def mapping_missing_folder(tmp_path, root_movie_dir, output_path):

    dirs = [
        root_movie_dir / "1999 The Matrix",
        root_movie_dir / "2003 The Matrix Reloaded",
    ]

    mapping = pd.DataFrame(
        {
            "disk_path": dirs,
            "tmdb_id": [603, 604],
            "tmdb_id_man": [NA_VALUE, NA_VALUE],
        }
    )

    mapping.to_csv(output_path / "mapping.csv", index=False)


@pytest.fixture
def mapping_missing_tmdb_id(tmp_path, root_movie_dir, output_path):

    dirs = [
        root_movie_dir / "1999 The Matrix",
        root_movie_dir / "2003 The Matrix Reloaded",
        root_movie_dir / "2003 The Matrix Revolutions",
    ]

    mapping = pd.DataFrame(
        {
            "disk_path": dirs,
            "tmdb_id": [603, 604, NA_VALUE],
            "tmdb_id_man": [NA_VALUE, NA_VALUE, NA_VALUE],
        }
    )

    mapping.to_csv(output_path / "mapping.csv", index=False)


@pytest.fixture
def full_mapping(tmp_path, root_movie_dir, output_path):

    dirs = []
    for folder in root_movie_dir.iterdir():
        if folder.is_dir():
            dirs.append(folder)

    mapping = pd.DataFrame(
        {
            "disk_path": dirs,
            "tmdb_id": [603, 604, 605],
            "tmdb_id_man": [NA_VALUE, NA_VALUE, NA_VALUE],
        }
    )

    mapping.to_csv(output_path / "mapping.csv", index=False)


@pytest.fixture
def output_path(tmp_path):
    output_path = tmp_path / "output"
    output_path.mkdir()
    return output_path


def test_empty_rmd(tmp_path, output_path):
    rmd = tmp_path / "rmd"
    rmd.mkdir()
    t = movieparse(rmd, output_path)

    t.list_dirs()
    assert t.mapping.shape[0] == 0
    assert t.mapping.shape[1] == MAPPING_COL_AMOUNT
    assert set(t.mapping.columns) == MAPPING_COLS

    t.update_mapping()
    t.get_ids()
    t.update_lookup_ids()


def test_run_once(root_movie_dir, output_path):
    t = movieparse(root_movie_dir, output_path)

    t.list_dirs()
    assert t.mapping.shape[0] == 3
    assert t.mapping.shape[1] == MAPPING_COL_AMOUNT
    assert set(t.mapping.columns) == MAPPING_COLS

    t.update_mapping()
    assert t.mapping.shape[0] == 3
    assert t.mapping.shape[1] == MAPPING_COL_AMOUNT

    t.get_ids()
    assert set(t.mapping["tmdb_id"]) == set([603, 604, 605])
    assert set(t.mapping["tmdb_id_man"]) == set([0])

    t.update_lookup_ids()
    assert set(t.lookup_ids) == set([603, 604, 605])


def test_run_full_cached(root_movie_dir, output_path, full_mapping):
    t = movieparse(root_movie_dir, output_path)
    assert t.cached_mapping.shape[0] == 3
    assert t.cached_mapping.shape[1] == MAPPING_COL_AMOUNT
    assert set(t.cached_mapping.columns) == MAPPING_COLS
    assert set(t.cached_metadata_ids) == set([603, 604, 605])

    t.list_dirs()
    assert t.mapping.shape[0] == 3
    assert t.mapping.shape[1] == MAPPING_COL_AMOUNT
    assert set(t.mapping.columns) == MAPPING_COLS

    t.update_mapping()
    assert t.mapping.shape[0] == 3
    assert t.mapping.shape[1] == MAPPING_COL_AMOUNT

    t.get_ids()
    assert set(t.mapping["tmdb_id"]) == set([603, 604, 605])
    assert set(t.mapping["tmdb_id_man"]) == set([0])

    t.update_lookup_ids()
    assert set(t.lookup_ids) == set()


def test_run_missing_folder(root_movie_dir, output_path, mapping_missing_folder):
    t = movieparse(root_movie_dir, output_path)
    assert t.cached_mapping.shape[0] == 2
    assert t.cached_mapping.shape[1] == MAPPING_COL_AMOUNT
    assert set(t.cached_mapping.columns) == MAPPING_COLS
    assert set(t.cached_metadata_ids) == set([603, 604])

    t.list_dirs()
    assert t.mapping.shape[0] == 3
    assert t.mapping.shape[1] == MAPPING_COL_AMOUNT
    assert set(t.mapping.columns) == MAPPING_COLS

    t.update_mapping()
    assert t.mapping.shape[0] == 3
    assert t.mapping.shape[1] == MAPPING_COL_AMOUNT

    t.get_ids()
    assert set(t.mapping["tmdb_id"]) == set([603, 604, 605])
    assert set(t.mapping["tmdb_id_man"]) == set([0])

    t.update_lookup_ids()
    assert set(t.lookup_ids) == set([605])


def test_run_missing_tmdb_id(root_movie_dir, output_path, mapping_missing_tmdb_id):
    t = movieparse(root_movie_dir, output_path)
    assert t.cached_mapping.shape[0] == 3
    assert t.cached_mapping.shape[1] == MAPPING_COL_AMOUNT
    assert set(t.cached_mapping.columns) == MAPPING_COLS

    t.list_dirs()
    assert t.mapping.shape[0] == 3
    assert t.mapping.shape[1] == MAPPING_COL_AMOUNT
    assert set(t.mapping.columns) == MAPPING_COLS

    t.update_mapping()
    assert t.mapping.shape[0] == 3
    assert t.mapping.shape[1] == MAPPING_COL_AMOUNT

    t.get_ids()
    assert set(t.mapping["tmdb_id"]) == set([603, 604, 605])
    assert set(t.mapping["tmdb_id_man"]) == set([0])

    t.update_lookup_ids()
    assert set(t.lookup_ids) == set([605])


def test_force_id_update(root_movie_dir, output_path, mapping_outdated_tmdb_id):

    t = movieparse(root_movie_dir, output_path, force_id_update=True)
    t.list_dirs()
    t.update_mapping()
    t.get_ids()
    t.update_lookup_ids()
    assert set(t.lookup_ids) == set([603, 604, 605])
