# movieparse

movieparse is a lazy utility for looking up movie metadata from [TMDB](https://www.themoviedb.org/) using movie release year and title. It has both an
Python API and CLI.

## Installation

tbd.

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

Contents inside the subfolder aren't taken into consideration.

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
you can add the `tmdb_id_man` manually:

| disk_path                       | tmdb_id | tmdb_id_man |
| ------------------------------- | ------- | ----------- |
| /root_movie_dir/1999 The Martix | -1      | `603`       |

The next time you use the parser, that manual id will be looked up.

### Caching

Metadata and TMDB Ids are only looked up again if they're not in the current data.

### Schemas

The following files will be written:

```
mapping.csv                         genres.csv
    tmdb_id                             genres.id
    tmdb_id_man                         genres.name
    disk_path                           tmdb_id

details.csv                         spoken_languages.csv
    m.adult                             spoken_languages.english_name
    m.backdrop_path                     spoken_languages.iso_639_1
    m.budget                            spoken_languages.name
    m.homepage                          tmdb_id
    m.imdb_id
    m.original_language
    m.original_title                production_companies.csv
    m.overview                          production_companies.id
    m.popularity                        production_companies.logo_path
    m.poster_path                       production_companies.name
    m.release_date                      production_companies.origin_country
    m.revenue                           tmdb_id
    m.runtime
    m.status                        production_countries.csv
    m.tagline                           production_countries.iso_3166_1
    m.title                             production_countries.name
    m.video                             tmdb_id
    m.vote_average
    m.vote_count
    m.belongs_to_collection.id
    m.belongs_to_collection.name
    m.belongs_to_collection.poster_path
    m.belongs_to_collection.backdrop_path
    tmdb_id
    m.belongs_to_collection

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
