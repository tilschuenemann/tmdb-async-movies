"""Module to use Movieparse with CLI."""

from pathlib import Path
from typing import List

import click
from click import Context

from movieparse.main import Movieparse


@click.group()
@click.option(
    "-t",
    "--tmdb-api-key",
    type=str,
    help="TMDB API Key. Falls back to environment variable TMDB_API_KEY.",
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
    help="Output directory where files get written to.",
)
@click.option(
    "-lx",
    "--lax",
    is_flag=True,
    default=False,
    show_default=True,
    help=" Always use title and release year for looking up metadata, no fallback to title only.",
)
@click.option(
    "-p",
    "--parsing_style",
    type=click.IntRange(-1, 1),
    default=-1,
    show_default=True,
    help="Define parsing style to use. -1 for estimating parsing style.",
)
@click.option(
    "-l",
    "--language",
    type=str,
    help="ISO-639-1 shortcode for getting locale information.",
)
@click.pass_context
def cli(
    ctx: Context,
    tmdb_api_key: str | None,
    output_dir: Path | None,
    lax: bool,
    parsing_style: int,
    language: str,
) -> None:
    """Take general arguments and pass them as context object."""
    ctx.ensure_object(dict)
    ctx.obj["tmdb_api_key"] = tmdb_api_key
    ctx.obj["output_dir"] = output_dir
    ctx.obj["lax"] = lax
    ctx.obj["parsing_style"] = parsing_style
    ctx.obj["language"] = language


@cli.command("dir", help="Use ROOT_MOVIE_DIRs subfolder names to lookup metadata.")
@click.argument(
    "root_movie_dir",
    required=True,
    nargs=1,
    type=click.Path(path_type=Path, exists=True, file_okay=False, dir_okay=True),
)
@click.pass_context
def from_dir(ctx: Context, root_movie_dir: Path) -> None:
    """Lookup movies from given root_movie_dir.

    Args:
      ctx: context passed from cli options.
      root_movie_dir: directory where movie subfolders lie.
    """
    tmdb_api_key = ctx.obj["tmdb_api_key"]
    output_dir = ctx.obj["output_dir"]
    lax = ctx.obj["lax"]
    parsing_style = ctx.obj["parsing_style"]
    language = ctx.obj["language"]
    root_movie_dir = Path(root_movie_dir)

    m = Movieparse(
        tmdb_api_key=tmdb_api_key,
        output_dir=output_dir,
        strict=lax,
        parsing_style=parsing_style,
        language=language,
    )
    m.parse_root_movie_dir(root_movie_dir)


@cli.command("list", help="Use given MOVIELIST to lookup metadata.")
@click.argument("movielist", nargs=-1, required=True)
@click.pass_context
def from_list(ctx: Context, movielist: List[str]) -> None:
    """Lookup movies from given movielist.

    Args:
      ctx: context passed from cli options.
      movielist: List of titles (and optionally release years).
    """
    tmdb_api_key = ctx.obj["tmdb_api_key"]
    output_dir = ctx.obj["output_dir"]
    lax = ctx.obj["lax"]
    parsing_style = ctx.obj["parsing_style"]
    language = ctx.obj["language"]

    m = Movieparse(
        tmdb_api_key=tmdb_api_key,
        output_dir=output_dir,
        strict=lax,
        parsing_style=parsing_style,
        language=language,
    )
    m.parse_movielist(movielist)


if __name__ == "__main__":
    cli()
