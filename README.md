# Movieparse

[![PyPI](https://img.shields.io/pypi/v/movieparse.svg)][pypi_]
[![Status](https://img.shields.io/pypi/status/movieparse.svg)][status]
[![Python Version](https://img.shields.io/pypi/pyversions/movieparse)][python version]
[![License](https://img.shields.io/pypi/l/movieparse)][license]

[![Read the documentation at https://movieparse.readthedocs.io/](https://img.shields.io/readthedocs/movieparse/latest.svg?label=Read%20the%20Docs)][read the docs]
[![Tests](https://github.com/tilschuenemann/movieparse/workflows/Tests/badge.svg)][tests]
[![Codecov](https://codecov.io/gh/tilschuenemann/movieparse/branch/main/graph/badge.svg)][codecov]

[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)][pre-commit]
[![Black](https://img.shields.io/badge/code%20style-black-000000.svg)][black]

[pypi_]: https://pypi.org/project/movieparse/
[status]: https://pypi.org/project/movieparse/
[python version]: https://pypi.org/project/movieparse
[read the docs]: https://movieparse.readthedocs.io/
[tests]: https://github.com/tilschuenemann/movieparse/actions?workflow=Tests
[codecov]: https://app.codecov.io/gh/tilschuenemann/movieparse
[pre-commit]: https://github.com/pre-commit/pre-commit
[black]: https://github.com/psf/black

## Features

`movieparse` is an asynchronous utility for fetching bulk movie data from [TMDB](https://www.themoviedb.org/) using movie title and optionally release year. It has both a Python API and a CLI.

Distinction from other packages, `movieparse`:

- focuses on fetching movies only.
- can write metadata as CSV files, but is also keeps them within the movieparse object.
- makes all API requests asynchronously and is therefore very fast.
- casts all metadata dtypes so you don't have to.
- can uses multiple sources of input and is easily extendable, as long as the input features movie title and release year.

## Requirements

You'll need to have a TMDB API key in order to make API requests. Either specify it on initialization of Movieparse or add it as environment variable:

```bash
$ export TMDB_API_KEY="your_api_key_here"
```

## Installation

You can install _Movieparse_ via [pip] from [PyPI]:

```console
$ pip install movieparse
```

## Usage

Please see the [Command-line Reference] for details.

## Contributing

Contributions are very welcome.
To learn more, see the [Contributor Guide].

## License

Distributed under the terms of the [MIT license][license],
_Movieparse_ is free and open source software.

## Issues

If you encounter any problems,
please [file an issue] along with a detailed description.

## Credits

This project was generated from [@cjolowicz]'s [Hypermodern Python Cookiecutter] template.

[@cjolowicz]: https://github.com/cjolowicz
[pypi]: https://pypi.org/
[hypermodern python cookiecutter]: https://github.com/cjolowicz/cookiecutter-hypermodern-python
[file an issue]: https://github.com/tilschuenemann/movieparse/issues
[pip]: https://pip.pypa.io/

<!-- github-only -->

[license]: https://github.com/tilschuenemann/movieparse/blob/main/LICENSE
[contributor guide]: https://github.com/tilschuenemann/movieparse/blob/main/CONTRIBUTING.md
[command-line reference]: https://movieparse.readthedocs.io/en/latest/usage.html
