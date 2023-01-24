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

    def merge_author_names(self) -> None:
        """Replace all known versions of author names (translations, misspellings) with one primary name.

        All author name versions should be listed as links in one author file -
        just copy them from other author files to that `primary` author file.
        """
        for review in self.reviews.values():
            if (
                review.author in self.authors
                and review.author != self.authors[review.author].author
            ):
                # we should update author name in the review
                # and series links
                pass
        for author in self.authors.values():
            # delete author files for non-main author name
            # rename book series files if they exist for non-main author names
            if author:
                pass

    def dump(self, books: GoodreadsBooks) -> Tuple[int, int]:
        """Save books and authors as md-files.

        Returns (reviews_added, authors_added)
        """
        for subfolder in SUBFOLDERS.values():
            os.makedirs(self.folder / subfolder, exist_ok=True)

        reviews_added = 0
        authors_added = 0
        progress_reviews_title = tqdm(bar_format="{desc}", leave=False, position=1)
        progress_reviews = tqdm(books, desc="Reviews", unit=" book", leave=False, position=2)
        progress_authors_title = tqdm(bar_format="{desc}", leave=False, position=3)
        progress_authors = tqdm(desc="Authors", unit=" author", leave=False, position=4)
        for book in books:
            progress_reviews_title.set_description_str(book.title)
            progress_authors_title.set_description_str(book.author)
            if book.author in self.authors:
                book.author = self.authors[
                    book.author
                ].author  # use the same author name for all synonyms
            if book.book_id not in self.reviews:
                if book.author not in self.authors and self.create_author_md(book):
                    authors_added += 1
                    progress_authors.update()
                if self.create_book_md(book):
                    reviews_added += 1
            progress_reviews.update()

        progress_reviews.close()
        progress_authors.close()
        progress_reviews_title.close()
        progress_authors_title.close()

        return reviews_added, authors_added

    def create_book_md(self, book: Book) -> bool:
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

        Look for author synonyms inside files and connect them with `Primary` author file - file
        with multiple author links inside.
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
                if names_count := len(re.findall(pattern, author.content)):
                    for author_match in re.finditer(pattern, author.content):
                        if (
                            author_match[1] in authors
                            and names_count > 1
                            or author_match[1] not in authors
                        ):
                            # do not replace if there is only one link in the file to keep links
                            # to `primary` author from author files with multiple links
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
