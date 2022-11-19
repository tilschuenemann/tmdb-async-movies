"""Sphinx configuration."""
project = "Movieparse"
author = "Til Schünemann"
copyright = "2022, Til Schünemann"
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx_click",
    "myst_parser",
]
autodoc_typehints = "description"
html_theme = "furo"
