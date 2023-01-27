"""Create markdown files for book review and author."""
import os
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
        self.authors, self.primary_authors = self.load_authors(folder / SUBFOLDERS["authors"])

    def merge_author_names(self) -> None:
        """Replace all known versions of author names (translations, misspellings) with one primary name.

        All author name versions should be listed as links in one author file -
        just copy them from other author files to that `primary` author file.
        Reviews will be relinked to this file.
        """
        for review in self.reviews.values():
            if (
                review.author in self.authors
                and review.author != self.authors[review.author].author
            ):
                review.rename_author(self.authors[review.author].author)
        for author in self.primary_authors.values():
            assert author.names is not None  # to make mypy happy
            for name in author.names:
                if (
                    name != author.author
                    and (
                        author_file_path := self.folder
                        / SUBFOLDERS["authors"]
                        / f"{clean_file_name(name)}.md"
                    ).exists()
                ):
                    os.remove(author_file_path)

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
            author=self.authors[book.author].author
            if book.author in self.authors
            else book.author,
            book_id=book.book_id,
            rating=book.rating,
            isbn=book.isbn,
            isbn13=book.isbn13,
            series=book.series,
            review=book.review,
        )
        if book.review == "" and book.rating == 0:
            subfolder = SUBFOLDERS["toread"]
        else:
            subfolder = SUBFOLDERS["reviews"]
        book_markdown.folder = self.folder / subfolder
        if book.series:
            book_markdown.create_series_files()
        book_markdown.write()
        return True

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
                    folder=folder,
                    file_name=file_name.name,
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

    def load_authors(self, folder: Path) -> Tuple[Dict[str, AuthorFile], Dict[str, AuthorFile]]:
        """Load existed authors.

        Look for author synonyms inside files and connect them with `Primary` author file - file
        with multiple author links inside.
        Create dict with {author: AuthorFile}, for each synonym.
        Return (all-authors, primary-authors)
        """
        authors: Dict[str, AuthorFile] = {}
        primary_authors: Dict[str, AuthorFile] = {}
        for filename in folder.glob("*.md"):
            with open(filename, "r", encoding="utf8") as author_file:
                author = AuthorFile(
                    file_name=str(filename),
                    author=Path(filename).stem,
                    content=author_file.read(),
                )
                assert author.names is not None  # to make mypy happy
                if len(author.names):
                    primary_file = (
                        len(author.names) > 1
                    )  # relink to primary file - with author names list
                    if primary_file:
                        primary_authors[author.author] = author
                    for name in author.names + [author.author]:  # + [author.author] to add
                        # `author` created from the file name, it's not necessary in the links inside the file
                        if name in authors and primary_file or name not in authors:
                            assert (
                                name not in authors
                                or author.author == authors[name].author
                                or len(authors[name].names) < 2  # type: ignore
                            ), (
                                f"Multiple author files `{author.author}` and `{authors[name].author}`"
                                " with name versions - should be only one `Primary` file"
                                " with multiple name versions."
                            )
                            authors[name] = author
                else:
                    self.skipped_unknown_files += 1
        return authors, primary_authors
