import argparse
import pathlib
from movieparse.main import movieparse


def main():
    parser = argparse.ArgumentParser(prog="tmdb_parser")
    parser.add_argument("root_movie_dir", nargs=1, type=pathlib.Path)
    parser.add_argument("--tmdb_api_key", nargs="?", type=str)
    parser.add_argument("--parsing_style", nargs="?", type=int, choices=[0, 1], const=0, default=0)
    parser.add_argument("--output_path", nargs="?", type=pathlib.Path)
    parser.add_argument("--lax", action="store_false")
    parser.add_argument("--language", nargs="?", type=str, const="en_US", default="en_US")

    args = parser.parse_args()

    m = movieparse(
        tmdb_api_key=args.tmdb_api_key,
        parsing_style=args.parsing_style,
        root_movie_dir=args.root_movie_dir[0],
        output_path=args.output_path,
        strict=args.lax,
        language=args.language,
    )

    m.parse()


if __name__ == "__main__":
    main()
