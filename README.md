![Test Badge](https://github.com/tilschuenemann/movieparse/actions/workflows/tests.yml/badge.svg)

# movieparse

`movieparse` is a lazy utility for fetching bulk movie data from [TMDB](https://www.themoviedb.org/) using movie release year and title. It has both an
Python API and CLI.

## Installation & Requirements

```bash
pip install movieparse
```

You'll need to have a TMDB API key in order to make API requests. Either specify it explicitly or add it as environment variable:

```bash
export TMDB_API_KEY="your_api_key_here"
```

## Usage

This program assumes that your root movie folder looks like this:

```
root_movie_dir/
    1999 The Matrix/
        thematrix.mkv
    1999 Fight Club/
        fightclub-part1.mkv
        fightclub-part2.mkv
        fightclub.srt
```

Contents inside the subfolder aren't taken into consideration. Running without further options:

```bash
movieparse root_movie_dir/
```

Additional options:

```bash
movieparse -h
usage: tmdb_parser [-h] [--root_movie_dir [ROOT_MOVIE_DIR] | --movie_list MOVIE_LIST [MOVIE_LIST ...]] [--tmdb_api_key [TMDB_API_KEY]]
                   [--parsing_style [{0,1}]] [--output_path [OUTPUT_PATH]] [--lax] [--language [LANGUAGE]] [--eager]

options:
  -h, --help            show this help message and exit
  --root_movie_dir [ROOT_MOVIE_DIR]
                        Directory containing your movie folders.
  --movie_list MOVIE_LIST [MOVIE_LIST ...]
                        Alternative to root_movie_dir, takes list of strings with movie title and optionally movie release year.
  --tmdb_api_key [TMDB_API_KEY]
                        TMDB API key. If not supplied here, environment variable TMDB_API_KEY will be read.
  --parsing_style [{0,1}]
                        Naming convention used - see documentation for examples.
  --output_path [OUTPUT_PATH]
                        Path to directory where output CSVs get written to. Defaults to current directory.
  --lax                 Use if TMDB ID lookup should fall back to title only (instead of year+title). Results may not be as accurate.
  --language [LANGUAGE]
                        ISO-639-1 language shortcode for specifying result language. Defaults to en_US.
  --eager               Using this will refetch all IDs and metadata without accessing the cache.
```

## Features

### Different Naming Conventions Supported

Currently these naming conventions are supported:

| parsing_style | Example           |
| ------------- | ----------------- |
| 0             | 1999 The Matrix   |
| 1             | 1999 - The Matrix |

Every parsing style is a regex pattern - incase you want to use a parsing style that's not supported, create a pull request and add yours!

### Custom Lookup

After parsing your files, take a look into mapping.csv:

| disk_path                       | tmdb_id | tmdb_id_man |
| ------------------------------- | ------- | ----------- |
| /root_movie_dir/1999 The Martix | -1      | 0           |

For some movies the correct TMDB Id cant be looked up due to bad spelling or old year-title combinations. For these movies
you can add the _tmdb_id_man_ manually:

| disk_path                       | tmdb_id | tmdb_id_man |
| ------------------------------- | ------- | ----------- |
| /root_movie_dir/1999 The Martix | -1      | _603_       |

The next time you use `movieparse` the manual id will be looked up.

### Caching

If you ran `movieparse` successfully, the mapping and metadata files will be written to disk. The next time you run it, only new paths will be appended to your mapping and metadata will be only looked up if it's not present in the current metadata.

You can disable this behavior by using the `--eager` flag in the CLI.

### Schemas

The following files will be written:

```
mapping.csv                         genres.csv
    tmdb_id                             genres.id
    tmdb_id_man                         genres.name
    disk_path                           tmdb_id

details.csv                         spoken_languages.csv
    adult                               spoken_languages.english_name
    backdrop_path                       spoken_languages.iso_639_1
    budget                              spoken_languages.name
    homepage                            tmdb_id
    imdb_id
    original_language
    original_title                  production_companies.csv
    overview                            production_companies.id
    popularity                          production_companies.logo_path
    poster_path                         production_companies.name
    release_date                        production_companies.origin_country
    revenue                             tmdb_id
    runtime
    status                          production_countries.csv
    tagline                             production_countries.iso_3166_1
    title                               production_countries.name
    video                               tmdb_id
    vote_average
    vote_count                      collections.csv
    tmdb_id                             collection.id
                                        collection.name
                                        collection.poster_path
                                        collection.backdrop_path
                                        tmdb_id

cast.csv                            crew.csv
    cast.adult                          crew.adult
    cast.gender                         crew.gender
    cast.id                             crew.id
    cast.known_for_department           crew.known_for_department
    cast.name                           crew.name
    cast.original_name                  crew.original_name
    cast.popularity                     crew.popularity
    cast.profile_path                   crew.profile_path
    cast.cast_id                        crew.credit_id
    cast.character                      crew.department
    cast.credit_id                      crew.job
    cast.order                          tmdb_id
    tmdb_id
```

## For Developers

The movieparse object exposes the following methods and attributes:

`moviesyms.parse()`

1. It saves all directories inside root_movie_dir in the mapping dataframe.
2. Mapping is appended to the cached_mapping which was created during initialization. User-supplied tmdb_id_mans are kept while duplicate paths are dropped.
3. Title and possibly year are extracted from each folder name and the TMDB API is queried for getting the TMDB ID, which is appended in mapping. Mapping.csv gets written.
4. A set of tmdb_ids and tmdb_id_mans is created for looking up the metadata (cached tmdb_ids are excluded if specified).
5. Metadata is looked up from the newly created set.

`moviesyms.write()`

- Writes all non-empty metadata tables to output_path destination.

Mapping:

- `moviesyms.mapping`

Metadata dataframes:

- `moviesyms.cast`
- `moviesyms.collect`
- `moviesyms.crew`
- `moviesyms.details`
- `moviesyms.genres`
- `moviesyms.prod_comp`
- `moviesyms.prod_count`
- `moviesyms.spoken_langs`

Caches:

- `moviesyms.cached_metadata_ids`
- `moviesyms.cached_ids`
- `moviesyms.cached_mapping`
