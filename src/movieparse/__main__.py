"""Command-line interface."""
import click


@click.command()
@click.version_option()
def main() -> None:
    """Movieparse."""


if __name__ == "__main__":
    main(prog_name="movieparse")  # pragma: no cover
