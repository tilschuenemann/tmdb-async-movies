# tmdbasync

[![PyPI](https://img.shields.io/pypi/v/tmdbasync.svg)][pypi_]
[![Status](https://img.shields.io/pypi/status/tmdbasync.svg)][status]
[![Python Version](https://img.shields.io/pypi/pyversions/tmdbasync)][python version]
[![License](https://img.shields.io/pypi/l/tmdbasync)][license]

[![Read the documentation at https://tmdbasync.readthedocs.io/](https://img.shields.io/readthedocs/tmdbasync/latest.svg?label=Read%20the%20Docs)][read the docs]
[![Tests](https://github.com/tilschuenemann/tmdbasync/workflows/Tests/badge.svg)][tests]
[![Codecov](https://codecov.io/gh/tilschuenemann/tmdbasync/branch/main/graph/badge.svg)][codecov]

[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)][pre-commit]
[![Black](https://img.shields.io/badge/code%20style-black-000000.svg)][black]

[pypi_]: https://pypi.org/project/tmdbasync/
[status]: https://pypi.org/project/tmdbasync/
[python version]: https://pypi.org/project/tmdbasync
[read the docs]: https://tmdbasync.readthedocs.io/
[tests]: https://github.com/tilschuenemann/tmdbasync/actions?workflow=Tests
[codecov]: https://app.codecov.io/gh/tilschuenemann/tmdbasync
[pre-commit]: https://github.com/pre-commit/pre-commit
[black]: https://github.com/psf/black

## Features

`tmdbasync` is an asynchronous utility for fetching bulk movie data from [TMDB](https://www.themoviedb.org/) using movie title and optionally release year. It has both a Python API and a CLI.

It's ready to

## Requirements

You'll need to have a TMDB API key in order to make API requests. Either specify it on initialization of tmdbasync or add it as environment variable:

```bash
$ export TMDB_API_KEY="your_api_key_here"
```

## Installation

You can install _tmdbasync_ via [pip] from [PyPI]:

```console
$ pip install tmdbasync
```

## Usage

Please see the [Command-line Reference] for details.

## Contributing

Contributions are very welcome.
To learn more, see the [Contributor Guide].

## License

Distributed under the terms of the [MIT license][license],
_tmdbasync_ is free and open source software.

## Issues

If you encounter any problems,
please [file an issue] along with a detailed description.

## Credits

This project was generated from [@cjolowicz]'s [Hypermodern Python Cookiecutter] template.

[@cjolowicz]: https://github.com/cjolowicz
[pypi]: https://pypi.org/
[hypermodern python cookiecutter]: https://github.com/cjolowicz/cookiecutter-hypermodern-python
[file an issue]: https://github.com/tilschuenemann/tmdbasync/issues
[pip]: https://pip.pypa.io/

<!-- github-only -->

[license]: https://github.com/tilschuenemann/tmdbasync/blob/main/LICENSE
[contributor guide]: https://github.com/tilschuenemann/tmdbasync/blob/main/CONTRIBUTING.md
[command-line reference]: https://tmdbasync.readthedocs.io/en/latest/usage.html
