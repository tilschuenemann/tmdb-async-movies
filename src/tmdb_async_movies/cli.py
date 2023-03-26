"""Module to use TMDBAsync with CLI."""

from pathlib import Path
from typing import Tuple

import click
from click import Context

from tmdb_async_movies.main import TmdbAsyncMovies


@click.group()
@click.option(
    "-t",
    "--tmdb-api-key",
    type=str,
    help="TMDB API Key. Falls back to environment variable TMDB_API_KEY if not specified.",
    default=None,
)
@click.option(
    "-o",
    "--output_dir",
    type=click.Path(
        path_type=Path,
        exists=True,
        file_okay=False,
        dir_okay=True,
        writable=True,
        readable=True,
    ),
    help="Output directory where metadata get written to.",
)
@click.option(
    "-a",
    "--include_adult",
    is_flag=True,
    default=True,
    show_default=True,
    help="Whether to include adult results.",
)
@click.option(
    "-l",
    "--language",
    type=str,
    default="en_US",
    show_default=True,
    help="ISO-639-1 shortcode for getting locale information.",
)
@click.option(
    "-n",
    "--naming_convention",
    type=click.IntRange(-1, 1),
    show_default=True,
    default=0,
    help="Define naming convention used for extracting title and year.",
)
@click.option(
    "-b",
    "--backup_call",
    is_flag=True,
    default=False,
    show_default=True,
    help="Whether to submit another query using title only if title + year yields no result.",
)
@click.pass_context
def tmdbasyncmovies(
    ctx: Context,
    tmdb_api_key: str | None,
    output_dir: Path | None,
    include_adult: bool,
    language: str,
    naming_convention: int,
    backup_call: bool,
) -> None:
    """Tmdbasync CLI."""
    ctx.ensure_object(dict)
    ctx.obj["tmdb_api_key"] = tmdb_api_key
    ctx.obj["output_dir"] = output_dir
    ctx.obj["include_adult"] = include_adult
    ctx.obj["language"] = language
    ctx.obj["naming_convention"] = naming_convention
    ctx.obj["backup_call"] = backup_call


@tmdbasyncmovies.command("from_dir", help="Use MOVIE_DIRs subfolders as queries.")
@click.argument(
    "movie_dir",
    required=True,
    nargs=1,
    type=click.Path(path_type=Path, exists=True, file_okay=False, dir_okay=True),
)
@click.pass_context
def from_dir(ctx: Context, movie_dir: Path) -> None:
    """Lookup movies from given movie_dir.

    Args:
      ctx: context passed from cli options.
      movie_dir: directory where movie subfolders lie.
    """
    tmdb_api_key = ctx.obj["tmdb_api_key"]
    output_dir = ctx.obj["output_dir"]
    include_adult = ctx.obj["include_adult"]
    language = ctx.obj["language"]
    naming_convention = ctx.obj["naming_convention"]
    backup_call = ctx.obj["backup_call"]

    t = TmdbAsyncMovies(
        tmdb_api_key=tmdb_api_key,
        include_adult=include_adult,
        language=language,
        naming_convention=naming_convention,
        backup_call=backup_call,
    )

    t.parse_movie_dirs(Path(movie_dir))
    t.write(output_dir)


@tmdbasyncmovies.command("from_input", help="Pass one or multiple queries.")
@click.argument("QUERIES", nargs=-1, type=str, required=True)
@click.pass_context
def from_input(ctx: Context, queries: Tuple[str]) -> None:
    """Lookup movies from given queries.

    Args:
      ctx: context passed from cli options.
      queries: List of titles (and optionally release years).
    """
    tmdb_api_key = ctx.obj["tmdb_api_key"]
    output_dir = ctx.obj["output_dir"]
    include_adult = ctx.obj["include_adult"]
    language = ctx.obj["language"]
    naming_convention = ctx.obj["naming_convention"]
    backup_call = ctx.obj["backup_call"]

    t = TmdbAsyncMovies(
        tmdb_api_key=tmdb_api_key,
        include_adult=include_adult,
        language=language,
        naming_convention=naming_convention,
        backup_call=backup_call,
    )

    t.generic_parse(list(queries))
    t.write(output_dir)


if __name__ == "__main__":
    tmdbasyncmovies()  # pragma: no cover
