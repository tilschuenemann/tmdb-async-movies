# tmdb-async-movies

[![PyPI](https://img.shields.io/pypi/v/tmdb-async-movies.svg)][pypi_]
[![Status](https://img.shields.io/pypi/status/tmdb-async-movies.svg)][status]
[![Python Version](https://img.shields.io/pypi/pyversions/tmdb-async-movies)][python version]
[![License](https://img.shields.io/pypi/l/tmdb-async-movies)][license]

[![Read the documentation at https://tmdb-async-movies.readthedocs.io/](https://img.shields.io/readthedocs/tmdb-async-movies/latest.svg?label=Read%20the%20Docs)][read the docs]
[![Tests](https://github.com/tilschuenemann/tmdb-async-movies/workflows/Tests/badge.svg)][tests]
[![Codecov](https://codecov.io/gh/tilschuenemann/tmdb-async-movies/branch/main/graph/badge.svg)][codecov]

[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)][pre-commit]
[![Black](https://img.shields.io/badge/code%20style-black-000000.svg)][black]

[pypi_]: https://pypi.org/project/tmdb-async-movies/
[status]: https://pypi.org/project/tmdb-async-movies/
[python version]: https://pypi.org/project/tmdb-async-movies
[read the docs]: https://tmdb-async-movies.readthedocs.io/
[tests]: https://github.com/tilschuenemann/tmdb-async-movies/actions?workflow=Tests
[codecov]: https://app.codecov.io/gh/tilschuenemann/tmdb-async-movies
[pre-commit]: https://github.com/pre-commit/pre-commit
[black]: https://github.com/psf/black

## Features

`tmdb-async-movies` is an asynchronous utility for fetching bulk movie data from [TMDB](https://www.themoviedb.org/) using movie title and optionally release year.

- Designed for bulk usage: Pipe in a list of queries and get results immediately.
- Blazing fast: Asynchronous calls enable you to get metadata from hundreds of movies in a couple of seconds.
- Typed: Metadata dataframes are strictly cast so you don't have to do it yourself.
- Hackable: It's a small project with ~500 LOC.
- Accessible: It has both a Python API and a CLI.

## Requirements

You'll need to have a TMDB API key in order to make API requests.

Default environment variable:

```bash
$ export TMDB_API_KEY="your_api_key_here"
```

Python:

```python
from tmdb_async_movies.main import TmdbAsyncMovies
t = TmdbAsyncMovies(tmdb_api_key="your_api_key_here")
```

CLI:

```bash
tmdb-async-movies -t "your_api_key_here" from_input "1999 The Matrix"
```

## Installation

You can install _tmdb-async-movies_ via [pip] from [PyPI]:

```console
$ pip install tmdb-async-movies
```

## Documentation

Please see the [documentation] for details.

## Contributing

Contributions are very welcome.
To learn more, see the [Contributor Guide].

## License

Distributed under the terms of the [MIT license][license],
_tmdb_async_movies_ is free and open source software.

## Issues

If you encounter any problems,
please [file an issue] along with a detailed description.

## Credits

This project was generated from [@cjolowicz]'s [Hypermodern Python Cookiecutter] template.

[@cjolowicz]: https://github.com/cjolowicz
[pypi]: https://pypi.org/
[hypermodern python cookiecutter]: https://github.com/cjolowicz/cookiecutter-hypermodern-python
[file an issue]: https://github.com/tilschuenemann/tmdb-async-movies/issues
[pip]: https://pip.pypa.io/

<!-- github-only -->

[license]: https://github.com/tilschuenemann/tmdb-async-movies/blob/main/LICENSE
[contributor guide]: https://github.com/tilschuenemann/tmdb-async-movies/blob/main/CONTRIBUTING.md
[documentation]: https://tmdb-async-movies.readthedocs.io/en/latest/
