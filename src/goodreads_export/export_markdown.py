"""Create markdown files for book review and author."""
import os
import urllib.parse
from pathlib import Path
from typing import Dict, Optional

import pandas as pd
from tqdm import tqdm

from goodreads_export.goodreads_review import Book


def dump_md(books_df: pd.DataFrame, folder: Path) -> None:
    """Save books and authors as md-files."""
    for subfolder in SUBFOLDERS.values():
        os.makedirs(folder / subfolder)

    progress_review = tqdm(books_df, unit="book", leave=False)
    progress_author = tqdm(unit="author", leave=False)
    reviews_added = 0
    authors_added = 0

    for _, goodreads_book in books_df.iterrows():
        progress_review.update(1)
        progress_review.set_description(goodreads_book["Title"])
        book = Book(goodreads_book)
        author_file_name = create_author_md(book, folder)
        if author_file_name is not None:
            authors_added += 1
            progress_author.update(1)
            progress_author.set_description(author_file_name)
        book_file_name = create_book_md(book, folder)
        if book_file_name is not None:
            reviews_added += 1

    progress_review.close()
    progress_author.close()
    print(f"\nAdded {reviews_added} reviews, {authors_added} authors")


FILE_NAME_REPLACE_MAP = {
    "%": " percent",
    ":": "",
    "/": "_",
    ",": ";",
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


def create_book_md(book: Book, folder: Path) -> Optional[str]:
    """Create book markdown file.

    Return None if the review file had already existed or return
    the added file name if new file was added
    """
    book.tags.append("#book/book")
    if book.rating > 0:
        book.tags.append(f"#book/rating{book.rating}")
    if book.review == "" and book.rating == 0:
        subfolder = SUBFOLDERS["toread"]
    else:
        subfolder = SUBFOLDERS["reviews"]
    file_name = f"{clean_filename(book.author)} - {clean_filename(book.title)}.md"
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
    return file_name


def create_author_md(book: Book, folder: Path) -> Optional[str]:
    """Create author markdown file.

    Return None if the author file had already existed or return
    the added file name if new file was added
    """
    author_file_name = f"{clean_filename(book.author)}.md"
    with open(
        folder / SUBFOLDERS["authors"] / author_file_name,
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
        return author_file_name
