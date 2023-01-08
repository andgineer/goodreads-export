"""Create md-files from https://www.goodreads.com/ CSV export."""
import os
import sys
import urllib.parse
from pathlib import Path
from typing import Dict, Optional, TextIO

import click
import markdownify
import pandas as pd

from goodreads_export.version import VERSION

FILE_NAME_REPLACE_MAP = {
    "%": " percent",
    ":": "",
    "/": "_",
    ",": ";",
    ".": "",
    "\\": "_",
    "[": "(",
    "]": ")",
    "<": "(",
    ">": ")",
    "*": "x",
    "?": "",
    '"': "'",
    "|": "_",
    "#": "@",
}


def clean_filename(file_name: str, replace_map: Optional[Dict[str, str]] = None) -> str:
    """Replace chars unsafe for file name."""
    if replace_map is None:
        replace_map = FILE_NAME_REPLACE_MAP
    return "".join(replace_map.get(ch, ch) for ch in file_name)


def load_reviews(csv_file: TextIO) -> pd.DataFrame:
    """Load goodreads books infor from CSV export."""
    return pd.read_csv(csv_file)


SUBFOLDERS = {
    "toread": "toread",  # for books without review and rating - supposedly this is from to-read
    "reviews": "reviews",  # all other books
    "authors": "authors",  # book authors
}


class Book:  # pylint: disable=too-few-public-methods,too-many-instance-attributes
    """Extract book description from goodreads export."""

    def __init__(self, goodreads: pd.Series) -> None:
        """Init the object from goodreads export."""
        self.title = goodreads["Title"]
        self.author = goodreads["Author"]
        self.book_id = goodreads["Book Id"]
        self.rating = goodreads["My Rating"]
        self.stars = "" if self.rating == 0 else ("@" * self.rating).ljust(6, " ")
        if isinstance(goodreads["My Review"], str):
            self.review = markdownify.markdownify(goodreads["My Review"])
        else:
            self.review = ""
        if not isinstance(goodreads["Bookshelves"], str):
            self.tags = []
        else:
            self.tags = [f"#book/{shelf.strip()}" for shelf in goodreads["Bookshelves"].split(",")]
        self.isbn = goodreads["ISBN"]
        self.isbn13 = goodreads["ISBN13"]


def dump_md(books_df: pd.DataFrame, folder: Path) -> None:
    """Save books and authors as md-files."""
    for subfolder in SUBFOLDERS.values():
        os.makedirs(folder / subfolder)

    for _, goodreads_book in books_df.iterrows():
        book = Book(goodreads_book)

        file_name = f"{book.stars}{clean_filename(book.author)} - {clean_filename(book.title)}.md"
        book_url = f"https://www.goodreads.com/book/show/{book.book_id}"

        book.tags.append("#book/book")
        if book.rating > 0:
            book.tags.append(f"#book/rating{book.rating}")
        with open(
            folder / SUBFOLDERS["authors"] / f"{clean_filename(book.author)}.md",
            "w",
            encoding="utf8",
        ) as md_file:
            author_article = f"{book.author}\n\n#book/author"
            md_file.write(author_article)
        if book.review == "" and book.rating == 0:
            subfolder = SUBFOLDERS["toread"]
        else:
            subfolder = SUBFOLDERS["reviews"]
        with open(folder / subfolder / file_name, "w", encoding="utf8") as md_file:
            book_article = f"""
[[{clean_filename(book.author)}]]: [{book.title}]({book_url})
ISBN{book.isbn} (ISBN13{book.isbn13})

{book.review}

[Search in Calibre](calibre://search/_?q={urllib.parse.quote(book.title)})

{" ".join(book.tags)}
"""
            md_file.write(book_article)


@click.command()
@click.argument(
    "csv_file",
    default="goodreads_library_export.csv",
    type=click.File("r"),
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
def main(csv_file: TextIO, output_folder: Path, version: bool) -> None:
    """Convert reviews and authors from goodreads export CSV file to markdown files.

    For example you can create nice structure in Obsidian.

    How to create goodreads export see in https://www.goodreads.com/review/import
    In 2022 they declare it to be removed by August,
    but at least at the end of 2022 it still works.

    CSV_FILE: Goodreads export file. By default `goodreads_library_export.csv`.

    Documentation https://andgineer.github.io/goodreads-export/
    """
    if version:
        print(f"{VERSION}")
        sys.exit(0)
    books = load_reviews(csv_file)
    dump_md(books, output_folder)


if __name__ == "__main__":
    main()  # pylint: disable=no-value-for-parameter
