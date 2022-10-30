import argparse
import pathlib
from movieparse.main import movieparse


def main():
    parser = argparse.ArgumentParser(prog="tmdb_parser")
    parser.add_argument("root_movie_dir", nargs=1, type=pathlib.Path, help="Directory containing your movie folders.")
    parser.add_argument("--tmdb_api_key", nargs="?", type=str,help="TMDB API key. If not supplied here, environment variable TMDB_API_KEY will be read.")
    parser.add_argument("--parsing_style", nargs="?", type=int, choices=[0, 1], const=0, default=0,help="Naming convention used - see documentation for examples.")
    parser.add_argument("--output_path", nargs="?", type=pathlib.Path, help="Path to directory where output CSVs get written to. Defaults to current directory.")
    parser.add_argument("--lax", action="store_false",help="Use if TMDB ID lookup should fall back to title only (instead of year+title). Results may not be as accurate.")
    parser.add_argument("--language", nargs="?", type=str, const="en_US", default="en_US",help="ISO-639-1 language shortcode for specifying result language. Defaults to en_US.")
    parser.add_argument("--eager", action="store_true", help="Using this will refetch all IDs and metadata without caching anything.")

    args = parser.parse_args()

    m = movieparse(
        tmdb_api_key=args.tmdb_api_key,
        parsing_style=args.parsing_style,
        root_movie_dir=args.root_movie_dir[0],
        output_path=args.output_path,
        strict=args.lax,
        language=args.language,
        force_id_update=args.eager,
        force_metadata_update=args.eager,
    )

    m.parse()
    m.write()


if __name__ == "__main__":
    main()
