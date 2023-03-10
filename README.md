# tmdbasyncmovies

[![PyPI](https://img.shields.io/pypi/v/tmdbasyncmovies.svg)][pypi_]
[![Status](https://img.shields.io/pypi/status/tmdbasyncmovies.svg)][status]
[![Python Version](https://img.shields.io/pypi/pyversions/tmdbasyncmovies)][python version]
[![License](https://img.shields.io/pypi/l/tmdbasyncmovies)][license]

[![Read the documentation at https://tmdbasyncmovies.readthedocs.io/](https://img.shields.io/readthedocs/tmdbasyncmovies/latest.svg?label=Read%20the%20Docs)][read the docs]
[![Tests](https://github.com/tilschuenemann/tmdbasyncmovies/workflows/Tests/badge.svg)][tests]
[![Codecov](https://codecov.io/gh/tilschuenemann/tmdbasyncmovies/branch/main/graph/badge.svg)][codecov]

[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)][pre-commit]
[![Black](https://img.shields.io/badge/code%20style-black-000000.svg)][black]

[pypi_]: https://pypi.org/project/tmdbasyncmovies/
[status]: https://pypi.org/project/tmdbasyncmovies/
[python version]: https://pypi.org/project/tmdbasyncmovies
[read the docs]: https://tmdbasyncmovies.readthedocs.io/
[tests]: https://github.com/tilschuenemann/tmdbasyncmovies/actions?workflow=Tests
[codecov]: https://app.codecov.io/gh/tilschuenemann/tmdbasyncmovies
[pre-commit]: https://github.com/pre-commit/pre-commit
[black]: https://github.com/psf/black

## Features

`tmdbasyncmovies` is an asynchronous utility for fetching bulk movie data from [TMDB](https://www.themoviedb.org/) using movie title and optionally release year. It has both a Python API and a CLI.

It's ready to

## Requirements

You'll need to have a TMDB API key in order to make API requests. Either specify it on initialization of tmdbasyncmovies or add it as environment variable:

```bash
$ export TMDB_API_KEY="your_api_key_here"
```

## Installation

You can install _tmdbasyncmovies_ via [pip] from [PyPI]:

```console
$ pip install tmdbasyncmovies
```

## Usage

Please see the [Command-line Reference] for details.

## Contributing

Contributions are very welcome.
To learn more, see the [Contributor Guide].

## License

Distributed under the terms of the [MIT license][license],
_tmdbasyncmovies_ is free and open source software.

## Issues

If you encounter any problems,
please [file an issue] along with a detailed description.

## Credits

This project was generated from [@cjolowicz]'s [Hypermodern Python Cookiecutter] template.

[@cjolowicz]: https://github.com/cjolowicz
[pypi]: https://pypi.org/
[hypermodern python cookiecutter]: https://github.com/cjolowicz/cookiecutter-hypermodern-python
[file an issue]: https://github.com/tilschuenemann/tmdbasyncmovies/issues
[pip]: https://pip.pypa.io/

<!-- github-only -->

[license]: https://github.com/tilschuenemann/tmdbasyncmovies/blob/main/LICENSE
[contributor guide]: https://github.com/tilschuenemann/tmdbasyncmovies/blob/main/CONTRIBUTING.md
[command-line reference]: https://tmdbasyncmovies.readthedocs.io/en/latest/usage.html
