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
