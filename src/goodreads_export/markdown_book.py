"""Create markdown files for book review and author."""
import os
import urllib.parse
from pathlib import Path
from typing import Dict, Tuple

from tqdm import tqdm

from goodreads_export.author_file import AuthorFile
from goodreads_export.book_file import BookFile
from goodreads_export.clean_file_name import clean_file_name
from goodreads_export.goodreads_book import Book, GoodreadsBooks

SUBFOLDERS = {
    "toread": "toread",  # for books without review and rating - supposedly this is from to-read
    "reviews": "reviews",  # all other books
    "authors": "authors",  # book authors
}

REVIEWS_SUBFOLDERS = [SUBFOLDERS["reviews"], SUBFOLDERS["toread"]]


class BooksFolder:
    """Create markdown files for book review and author."""

    skipped_unknown_files = 0

    def __init__(self, folder: Path):
        """Initialize."""
        self.folder = folder
        self.reviews: Dict[str, BookFile] = {}
        for reviews_subfolder in REVIEWS_SUBFOLDERS:
            self.reviews |= self.load_reviews(folder / reviews_subfolder)
        self.authors = self.load_authors(folder / SUBFOLDERS["authors"])
        # todo add authors with more that one name to self.authors_to_merge

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
        book_markdown = BookFile(
            title=book.title,
            tags=book.tags,
            author=book.author,
            book_id=book.book_id,
            rating=book.rating,
            isbn=book.isbn,
            isbn13=book.isbn13,
            series=book.series_full,
            review=book.review,
        )
        if book.review == "" and book.rating == 0:
            subfolder = SUBFOLDERS["toread"]
        else:
            subfolder = SUBFOLDERS["reviews"]
        if book.series:
            self.create_series_mds(book, subfolder)
        book_markdown.write(self.folder / subfolder)
        return True

    def create_series_mds(self, book: Book, subfolder: str) -> None:
        """Create series files if id does not exist.

        Do not change already existed files.
        """
        for series_idx, series in enumerate(book.series_full):
            series_file_name = f"{clean_file_name(series)}.md"
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
                        f"""[[{clean_file_name(book.author)}]]
[{book.series[series_idx]}](https://www.goodreads.com/search?{search_params})"""
                    )

    def create_author_md(self, book: Book) -> bool:
        """Create author markdown if id does not exist.

        Do not change already existed file.

        Return True if author file was added, False otherwise
        """
        author_markdown = AuthorFile(
            author=book.author,
        )
        author_file_path = (
            self.folder  # type: ignore  # property and attr with the same name
            / SUBFOLDERS["authors"]
            / author_markdown.file_name
        )
        if not author_file_path.is_file():
            with author_file_path.open(
                "w",
                encoding="utf8",
            ) as md_file:
                md_file.write(author_markdown.content)  # type: ignore  # property and attr with the same name
                return True
        return False

    def load_reviews(self, folder: Path) -> Dict[str, BookFile]:
        """Load existed book reviews.

        Look for goodreads book ID inside files.
        Return {id: BookFile} for files with book ID, ignore other files.
        This way we ignore "- series" files and unknown files.
        """
        reviews: Dict[str, BookFile] = {}
        for file_name in folder.glob("*.md"):
            with open(file_name, "r", encoding="utf8") as review_file:
                book = BookFile(
                    title=Path(file_name).stem,
                    file_name=str(file_name),
                    content=review_file.read(),
                )
                if book.book_id is None:
                    self.skipped_unknown_files += 1
                elif book.book_id in reviews:
                    raise ValueError(
                        f"Duplicate book ID {book.book_id} in {file_name} "
                        f"and {reviews[book.book_id].file_name}"
                    )
                else:
                    reviews[book.book_id] = book
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
                assert author.names is not None  # to make mypy happy
                if len(author.names):
                    for name in author.names:
                        if name in authors and len(author.names) > 1 or name not in authors:
                            # do not replace if there is only one link in the file to keep links
                            # to `primary` author from author files with multiple links
                            authors[name] = author
                else:
                    self.skipped_unknown_files += 1
        return authors
