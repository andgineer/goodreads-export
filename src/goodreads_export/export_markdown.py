"""Create markdown files for book review and author."""
import os
import urllib.parse
from pathlib import Path
from typing import Dict, Optional

import pandas as pd

from goodreads_export.goodreads_review import Book


def dump_md(books_df: pd.DataFrame, folder: Path) -> None:
    """Save books and authors as md-files."""
    for subfolder in SUBFOLDERS.values():
        os.makedirs(folder / subfolder)

    for _, goodreads_book in books_df.iterrows():
        book = Book(goodreads_book)
        create_author_md(book, folder)
        create_book_md(book, folder)


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


SUBFOLDERS = {
    "toread": "toread",  # for books without review and rating - supposedly this is from to-read
    "reviews": "reviews",  # all other books
    "authors": "authors",  # book authors
}


def create_book_md(book: Book, folder: Path) -> None:
    """Create book markdown file."""
    book.tags.append("#book/book")
    if book.rating > 0:
        book.tags.append(f"#book/rating{book.rating}")
    if book.review == "" and book.rating == 0:
        subfolder = SUBFOLDERS["toread"]
    else:
        subfolder = SUBFOLDERS["reviews"]
    file_name = f"{book.stars}{clean_filename(book.author)} - {clean_filename(book.title)}.md"
    book_url = f"https://www.goodreads.com/book/show/{book.book_id}"
    with open(folder / subfolder / file_name, "w", encoding="utf8") as md_file:
        book_article = f"""
[[{clean_filename(book.author)}]]: [{book.title}]({book_url})
ISBN{book.isbn} (ISBN13{book.isbn13})

{book.review}

[Search in Calibre](calibre://search/_?q={urllib.parse.quote(book.title)})

{" ".join(book.tags)}
"""
        md_file.write(book_article)


def create_author_md(book: Book, folder: Path) -> None:
    """Create author markdown file."""
    with open(
        folder / SUBFOLDERS["authors"] / f"{clean_filename(book.author)}.md",
        "w",
        encoding="utf8",
    ) as md_file:
        search_params = urllib.parse.urlencode(
            {
                "utf8": "✓",
                "q": book.author,
                "search_type": "books",
                "search[field]": "author",
            }
        )
        author_article = f"""[{book.author}](https://www.goodreads.com/search?{search_params})

#book/author
"""
        md_file.write(author_article)
