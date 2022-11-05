import pytest
import pandas as pd
from movieparse.main import movieparse
import json


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
    tmp = root_movie_dir / "1979 Stalker"
    tmp.mkdir()
    return tmp


@pytest.fixture
def single_movie_conv2(root_movie_dir):
    tmp = root_movie_dir / "1979 - Stalker"
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


@pytest.fixture
def mapping_stub(output_path, multiple_movies):
    mapping_stub = pd.DataFrame({"disk_path": multiple_movies, "tmdb_id": [603, 604, 605], "tmdb_id_man": [0, 0, 777]})
    mapping_stub.to_csv((output_path / "mapping.csv"), index=False)
    return mapping_stub


@pytest.fixture
def details_stub(output_path):
    details_stub = pd.DataFrame({"tmdb_id": [603, 604, 605]})
    details_stub.to_csv((output_path / "details.csv"), index=False)
    return details_stub


def test_setup_caches(root_movie_dir, output_path, mapping_stub, multiple_movies):
    m = movieparse(root_movie_dir=root_movie_dir, output_path=output_path)

    assert set(m.cached_mapping_ids) == set([603, 604, 605])
    assert set(m.cached_mapping["disk_path"]) == set(multiple_movies)


def test_setup_caches_empty(root_movie_dir, output_path):
    m = movieparse(root_movie_dir, output_path)
    assert m.cached_mapping.empty
    assert set(m.cached_mapping_ids) == set()
    assert set(m.cached_metadata_ids) == set()


def test_read_existing(root_movie_dir, output_path, details_stub):
    m = movieparse(root_movie_dir, output_path)
    assert set(m.cached_metadata_ids) == set([603, 604, 605])
    assert m.details.empty is False


def test_estimate_parsing_style(output_path):
    l0 = []
    with pytest.raises(SystemExit, match="please supply a ROOT_MOVIE_DIR or a MOVIE_LIST!"):
        m = movieparse(output_path, movie_list=l0)
        m._create_mapping()
        m._guess_parsing_style()

    l1 = ["1999 The Matrix", "2003 The Matrix Reloaded", "2003 The Matrix Revolutions"]
    m = movieparse(output_path=output_path, movie_list=l1)
    m._create_mapping()
    m._guess_parsing_style()
    assert m._movieparse__PARSING_STYLE == 0

    l2 = ["1999 The Matrix", "2003 - The Matrix Reloaded"]
    m = movieparse(output_path=output_path, movie_list=l2)
    m._create_mapping()
    m._guess_parsing_style()
    assert m._movieparse__PARSING_STYLE == 0


def test_create_mapping_single(root_movie_dir, output_path, single_movie):
    m = movieparse(root_movie_dir, output_path)
    m._create_mapping()
    assert set(m.mapping["disk_path"]) == set([single_movie])
    assert m.mapping.shape == (1, 3)
    assert set(m.mapping.columns) == set(["disk_path", "tmdb_id", "tmdb_id_man"])


def test_create_mapping_multiple(root_movie_dir, output_path, multiple_movies):
    m = movieparse(root_movie_dir, output_path)
    m._create_mapping()
    assert set(m.mapping["disk_path"]) == set(multiple_movies)
    assert m.mapping.shape == (3, 3)
    assert set(m.mapping.columns) == set(["disk_path", "tmdb_id", "tmdb_id_man"])


def test_create_mapping_empty(root_movie_dir, output_path):
    m = movieparse(root_movie_dir, output_path)
    m._create_mapping()
    assert set(m.mapping["disk_path"]) == set()
    assert m.mapping.shape == (0, 3)
    assert set(m.mapping.columns) == set(["disk_path", "tmdb_id", "tmdb_id_man"])


def test_update_mapping_nocache(root_movie_dir, output_path, multiple_movies):
    m = movieparse(root_movie_dir, output_path)
    m._create_mapping()
    m._update_mapping()
    assert set(m.mapping["disk_path"]) == set(multiple_movies)
    assert set(m.mapping["tmdb_id_man"]) == set([0])
    assert set(m.mapping["tmdb_id"]) == set([0])


def test_update_mapping_cache(root_movie_dir, output_path, single_movie, mapping_stub):
    m = movieparse(root_movie_dir, output_path)
    m._create_mapping()
    m._update_mapping()
    assert m.mapping.shape == (4, 3)
    assert set(m.mapping["tmdb_id"]) == set([0, 603, 604, 605])
    assert set(m.mapping["tmdb_id_man"]) == set([0, 777])


def test_update_metadata_lookup_ids(root_movie_dir, output_path):
    cached_ids = [604]
    tmdb_ids = [-1, 604, 605, -2]
    tmdb_ids_man = [603, 0, 0, 0]

    # use cache
    m = movieparse(root_movie_dir, output_path, force_metadata_update=False)

    m.mapping = pd.DataFrame({"tmdb_id": tmdb_ids, "tmdb_id_man": tmdb_ids_man})
    m.cached_metadata_ids = set(cached_ids)

    m._update_metadata_lookup_ids()
    assert set(m.metadata_lookup_ids) == set([603, 605])
    assert set([-1, -2, -3, 0]) not in set(m.metadata_lookup_ids)

    # without cache
    m = movieparse(root_movie_dir, output_path, force_metadata_update=True)

    m.mapping = pd.DataFrame({"tmdb_id": tmdb_ids, "tmdb_id_man": tmdb_ids_man})
    m.cached_metadata_ids = set(cached_ids)

    m._update_metadata_lookup_ids()
    assert set(m.metadata_lookup_ids) == set([603, 604, 605])
    assert set([-1, -2, -3, 0]) not in set(m.metadata_lookup_ids)


def test_dissect_metadata(root_movie_dir, output_path, single_movie):
    m = movieparse(root_movie_dir, output_path)

    with open("tests/603_the_matrix.json", "r") as myfile:
        data = myfile.read()
    mock_response = json.loads(data)

    m._dissect_metadata_response(mock_response, 603)

    # correct records
    assert m.cast.shape[0] == 37
    assert m.collect.shape[0] == 1
    assert m.crew.shape[0] == 169
    assert m.details.shape[0] == 1
    assert m.genres.shape[0] == 2
    assert m.prod_comp.shape[0] == 4
    assert m.prod_count.shape[0] == 1

    # correct columns
    assert set(m.cast.columns) == set(
        [
            "cast.adult",
            "cast.gender",
            "cast.id",
            "cast.known_for_department",
            "cast.name",
            "cast.original_name",
            "cast.popularity",
            "cast.profile_path",
            "cast.cast_id",
            "cast.character",
            "cast.credit_id",
            "cast.order",
            "tmdb_id",
        ]
    )

    assert set(m.collect.columns) == set(
        ["collection.id", "collection.name", "collection.poster_path", "collection.backdrop_path", "tmdb_id"]
    )
    assert set(m.crew.columns) == set(
        [
            "crew.adult",
            "crew.gender",
            "crew.id",
            "crew.known_for_department",
            "crew.name",
            "crew.original_name",
            "crew.popularity",
            "crew.profile_path",
            "crew.credit_id",
            "crew.department",
            "crew.job",
            "tmdb_id",
        ]
    )
    assert set(m.details.columns) == set(
        [
            "adult",
            "backdrop_path",
            "budget",
            "homepage",
            "imdb_id",
            "original_language",
            "original_title",
            "overview",
            "popularity",
            "poster_path",
            "release_date",
            "revenue",
            "runtime",
            "status",
            "tagline",
            "title",
            "video",
            "vote_average",
            "vote_count",
            "tmdb_id",
        ]
    )
    assert set(m.prod_comp.columns) == set(
        [
            "production_companies.id",
            "production_companies.logo_path",
            "production_companies.name",
            "production_companies.origin_country",
            "tmdb_id",
        ]
    )
    assert set(m.prod_count.columns) == set(["production_countries.iso_3166_1", "production_countries.name", "tmdb_id"])
    assert set(m.spoken_langs.columns) == set(
        ["spoken_languages.english_name", "spoken_languages.iso_639_1", "spoken_languages.name", "tmdb_id"]
    )


def test_get_metadata_empty(root_movie_dir, output_path):
    m = movieparse(root_movie_dir, output_path, parsing_style=0)
    m.parse()


@pytest.mark.skip(reason="TBD: count function calls?")
def test_get_metadata(root_movie_dir, output_path, multiple_movies):
    m = movieparse(root_movie_dir, output_path)

    # with mock.patch.object(movieparse, '_dissect_response') as fake_increment:
    #     assert fake_increment.call_count == 0
    #     m.parse()
    #     assert fake_increment.call_count == 3


def test_write_empty(root_movie_dir, output_path):
    m = movieparse(root_movie_dir, output_path, parsing_style=0)
    m.parse()
    m.write()

    assert (output_path / "mapping.csv").exists()

    for metadata in [
        "cast",
        "crew",
        "collections",
        "details",
        "genres",
        "production_companies",
        "production_countries",
        "spoken_languages",
    ]:
        assert (output_path / f"{metadata}.csv").exists() is False


@pytest.mark.skip(reason="TBD: stub internal tables")
def test_write_multiple(root_movie_dir, output_path, multiple_movies):
    m = movieparse(root_movie_dir, output_path)

    # m.parse()
    m.write()

    for metadata in [
        "cast",
        "crew",
        "collections",
        "details",
        "genres",
        "mapping",
        "production_companies",
        "production_countries",
        "spoken_languages",
    ]:
        assert (output_path / f"{metadata}.csv").exists()


def test_e2e_badapikey(root_movie_dir, output_path, multiple_movies):
    m = movieparse(root_movie_dir=root_movie_dir, output_path=output_path, tmdb_api_key="wrongapikey")
    m.parse()
    assert set(m.mapping["tmdb_id_man"]) == set([0])
    assert set(m.mapping["disk_path"]) == set(multiple_movies)
    assert set(m.mapping["tmdb_id"]) == set([-3])

    assert m.cast.empty
    assert m.collect.empty
    assert m.crew.empty
    assert m.details.empty
    assert m.genres.empty
    assert m.prod_comp.empty
    assert m.prod_count.empty
    assert m.spoken_langs.empty
