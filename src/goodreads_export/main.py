"""Create md-files from https://www.goodreads.com/ CSV export."""
import os
import sys
from pathlib import Path

import click

from goodreads_export.goodreads_review import GoodreadsBooks
from goodreads_export.markdown_review import BooksFolder
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
def main(csv_file: str, output_folder: Path, version: bool) -> None:
    """Convert reviews and authors from goodreads export CSV file to markdown files.

    For example you can create nice structure in Obsidian.

    How to create goodreads export see in https://www.goodreads.com/review/import
    In 2022 they declare it to be removed by August,
    but at least at the end of 2022 it still works.

    CSV_FILE: Goodreads export file. By default `goodreads_library_export.csv`.
    if you specify just folder it will look for file with this name in that folder.

    Documentation https://andgineer.github.io/goodreads-export/
    """
    if version:
        print(f"{VERSION}")
        sys.exit(0)

    if os.path.isdir(csv_file):
        csv_file = os.path.join(csv_file, GOODREAD_EXPORT_FILE_NAME)
    if not os.path.isfile(csv_file):
        print(f"Goodreads export file '{csv_file}' not found.")
        sys.exit(1)

    try:
        books_folder = BooksFolder(output_folder)
        print(f"Reading existing files from {output_folder}...", end="")
        print(
            f" loaded {len(books_folder.reviews)} books, {len(books_folder.authors)} authors, "
            f"skipped {books_folder.skipped_unknown_files} unknown files"
        )

        print(f"Loading reviews from {csv_file}...", end="")
        books = GoodreadsBooks(csv_file)
        print(f" loaded {len(books)} reviews.")

        reviews_added, authors_added = books_folder.dump(books)
        print(f"\nAdded {reviews_added} review files, {authors_added} author files")

    except Exception as exc:  # pylint: disable=broad-except
        print(f"\n{exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()  # pylint: disable=no-value-for-parameter
