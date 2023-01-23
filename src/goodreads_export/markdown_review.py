"""Create markdown files for book review and author."""
import os
import re
import urllib.parse
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Tuple

from tqdm import tqdm

from goodreads_export.goodreads_review import Book, GoodreadsBooks

SUBFOLDERS = {
    "toread": "toread",  # for books without review and rating - supposedly this is from to-read
    "reviews": "reviews",  # all other books
    "authors": "authors",  # book authors
}


@dataclass
class BookFile:
    """Book file."""

    title: str
    file_name: str
    content: str
    author: Optional[str] = None
    book_id: Optional[str] = None

    # todo set_author() change content and set dirty flag


@dataclass
class AuthorFile:
    """Author file."""

    author: str
    file_name: str
    content: str


class BooksFolder:
    """Create markdown files for book review and author."""

    skipped_unknown_files = 0

    def __init__(self, folder: Path):
        """Initialize."""
        self.folder = folder
        self.reviews = self.load_reviews(folder / SUBFOLDERS["reviews"])
        self.reviews.update(self.load_reviews(folder / SUBFOLDERS["toread"]))
        self.authors = self.load_authors(folder / SUBFOLDERS["authors"])

    def dump(self, books: GoodreadsBooks) -> Tuple[int, int]:
        """Save books and authors as md-files.

        Returns (reviews_added, authors_added)
        """
        for subfolder in SUBFOLDERS.values():
            os.makedirs(self.folder / subfolder, exist_ok=True)

        progress_review = tqdm(books, unit="book", leave=False)
        progress_author = tqdm(unit="author", leave=False)
        reviews_added = 0
        authors_added = 0

        for book in books:
            progress_review.update()
            progress_review.set_description(book.title)
            progress_author.set_description(book.author)
            existing_review = self.reviews.get(book.book_id)
            if book.author in self.authors:
                author_name = self.authors[book.author].author
                book.author = author_name
                if existing_review and existing_review.author != author_name:
                    existing_review.author = (
                        author_name  # todo existing_review.set_author(author_name)
                    )

                book.author = self.authors[
                    book.author
                ].author  # use the same author name for all synonyms
            if book.book_id not in self.reviews:
                if book.author in self.authors and self.authors[book.author].author != book.author:
                    book.author = self.authors[
                        book.author
                    ].author  # use the same author name for all synonyms
                elif self.create_author_md(book):
                    authors_added += 1
                    progress_author.update()
                if self.create_book_md(book, existing_review):
                    reviews_added += 1

        progress_review.close()
        progress_author.close()
        return reviews_added, authors_added

    def create_book_md(self, book: Book, existed_file: Optional[BookFile]) -> bool:
        """Create book markdown file.

        Return True if book file was added or updated, False otherwise
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
        if book.series:
            self.create_series_mds(book, subfolder)
        # todo update review file with new author name if existed_file and existed_file.dirty
        if existed_file:
            pass
        with open(self.folder / subfolder / file_name, "w", encoding="utf8") as md_file:
            book_article = f"""
[[{clean_filename(book.author)}]]: [{book.title}]({book_url})
ISBN{book.isbn} (ISBN13{book.isbn13})
{' '.join(['[[' + clean_filename(series) + ']]' for series in book.series_full])}
{book.review}

[Search in Calibre](calibre://search/_?q={urllib.parse.quote(book.title)})

{" ".join(book.tags)}
"""
            md_file.write(book_article)
        return True

    def create_series_mds(self, book: Book, subfolder: str) -> None:
        """Create series files if id does not exist.

        Do not change already existed files.
        """
        for series_idx, series in enumerate(book.series_full):
            series_file_name = f"{clean_filename(series)}.md"
            search_params = urllib.parse.urlencode(
                {
                    "utf8": "✓",
                    "q": f"{book.series[series_idx]}, #",
                    "search_type": "books",
                    "search[field]": "title",
                }
            )
            series_file_path = self.folder / subfolder / series_file_name
            if not series_file_path.is_file():
                with series_file_path.open("w", encoding="utf8") as md_file:
                    md_file.write(
                        f"""[[{clean_filename(book.author)}]]
[{book.series[series_idx]}](https://www.goodreads.com/search?{search_params})"""
                    )

    def create_author_md(self, book: Book) -> bool:
        """Create author markdown if id does not exist.

        Do not change already existed file.

        Return True if author file was added, False otherwise
        """
        author_file_name = f"{clean_filename(book.author)}.md"
        author_file_path = self.folder / SUBFOLDERS["authors"] / author_file_name
        if not author_file_path.is_file():
            with author_file_path.open(
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
                return True
        return False

    def load_reviews(self, folder: Path) -> Dict[str, BookFile]:
        """Load existed book reviews.

        Look for goodreads book ID inside files.
        Return {id: BookFile} for files with book ID, ignore other files.
        """
        reviews = {}
        for filename in folder.glob("*.md"):
            with open(filename, "r", encoding="utf8") as review_file:
                book = BookFile(
                    title=Path(filename).stem, file_name=str(filename), content=review_file.read()
                )
                # todo move this code to BookFile
                pattern = (
                    r"\[\[([^]]+)\]\]: \[([^]]*)\]\(https://www\.goodreads\.com/book/show/(\d+)\)"
                )
                if (book_match := re.search(pattern, book.content)) is not None:
                    book.book_id = book_match[3]
                    book.title = book_match[2]
                    book.author = book_match[1]
                    reviews[book.book_id] = book
                else:
                    self.skipped_unknown_files += 1
        return reviews

    def load_authors(self, folder: Path) -> Dict[str, AuthorFile]:
        """Load existed authors.

        Look for author synonyms inside files.
        Return {author: AuthorFile}, for each synonym.
        """
        authors = {}
        for filename in folder.glob("*.md"):
            with open(filename, "r", encoding="utf8") as author_file:
                author = AuthorFile(
                    file_name=str(filename),
                    author=Path(filename).stem,
                    content=author_file.read(),
                )
                pattern = (
                    r"\[([^]]*)\]\(https://www\.goodreads\.com/search\?utf8=%E2%9C%93&q=[^&]*"
                    r"&search_type=books&search%5Bfield%5D=author\)"
                )
                if re.search(pattern, author.content) is not None:
                    for author_match in re.finditer(pattern, author.content):
                        authors[author_match[1]] = author
                else:
                    self.skipped_unknown_files += 1
        return authors


FILE_NAME_REPLACE_MAP = {
    "%": " percent",
    ":": "",
    "/": "_",
    ",": "",
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
