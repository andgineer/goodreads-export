"""Create md-files from https://www.goodreads.com/ CSV export."""
import os
import sys
from pathlib import Path

import click

from goodreads_export.goodreads_book import GoodreadsBooks
from goodreads_export.log import Log
from goodreads_export.markdown_book import BooksFolder
from goodreads_export.version import VERSION

GOODREAD_EXPORT_FILE_NAME = "goodreads_library_export.csv"


@click.command()
@click.argument(
    "csv_file",
    default=GOODREAD_EXPORT_FILE_NAME,
    nargs=1,
)
@click.option(
    "--out",
    "-o",
    "output_folder",
    default=".",
    type=click.Path(exists=True, path_type=Path),
    help="Folder where we put result. By default current folder.",
    nargs=1,
)
@click.option(
    "--version",
    "version",
    is_flag=True,
    default=False,
    help="Show version.",
    nargs=1,
)
@click.option(
    "--merge",
    "-m",
    "merge",
    is_flag=True,
    default=False,
    help="""Merge only. Use it if you need only re-link to primary author names
without importing goodreads file. See https://andgineer.github.io/goodreads-export/ for details.""",
    nargs=1,
)
@click.option(
    "--verbose",
    "-v",
    "verbose",
    is_flag=True,
    default=False,
    help="""Increase verbosity.""",
    nargs=1,
)
def main(csv_file: str, output_folder: Path, version: bool, merge: bool, verbose: bool) -> None:
    """Convert reviews and authors from goodreads export CSV file to markdown files.

    For example you can create nice structure in Obsidian.

    How to create goodreads export see in https://www.goodreads.com/review/import
    In 2022 they declare it to be removed by August,
    but at least at the end of 2022 it still works.

    CSV_FILE: Goodreads export file. By default `goodreads_library_export.csv`.
    if you specify just folder it will look for file with this name in that folder.

    Documentation https://andgineer.github.io/goodreads-export/
    """
    try:
        log = Log(verbose)
        if version:
            print(f"{VERSION}")
            sys.exit(0)

        if merge:  # merge only without import from goodreads file
            books = GoodreadsBooks(None)
        else:
            if os.path.isdir(
                csv_file
            ):  # if folder as csv_file try to find goodreads file in that folder
                csv_file = os.path.join(csv_file, GOODREAD_EXPORT_FILE_NAME)
            if not os.path.isfile(csv_file):
                print(f"Goodreads export file '{csv_file}' not found.")
                sys.exit(1)
            log.start(f"Loading reviews from {csv_file}")
            books = GoodreadsBooks(csv_file)
            print(f" loaded {len(books)} reviews.")

        books_folder = BooksFolder(output_folder)
        log.start(f"Reading existing files from {output_folder}")
        print(
            f" loaded {len(books_folder.reviews)} books, {len(books_folder.authors)} authors, "
            f"skipped {books_folder.stat.skipped_unknown_files} unknown files"
            f" and {books_folder.stat.series_added} series files.",
        )
        books_folder.merge_author_names()
        books_folder.dump(books, log)
        print(
            f"\nAdded {books_folder.stat.reviews_added} review files, "
            f"{books_folder.stat.authors_added} author files.",
            f"Renamed {books_folder.stat.authors_renamed} authors, "
            f"removed {books_folder.stat.author_names_removed} author names.",
        )

    except Exception as exc:  # pylint: disable=broad-except
        print(f"\n{exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()  # pylint: disable=no-value-for-parameter
