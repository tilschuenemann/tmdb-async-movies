"""Sphinx configuration."""
project = "tmdbasyncmovies"
author = "Til Schünemann"
copyright = "2023, Til Schünemann"
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx_click",
    "myst_parser",
    "sphinx_rtd_theme",
    "sphinx.ext.viewcode",
]
autodoc_typehints = "signature"
html_theme = "sphinx_rtd_theme"
