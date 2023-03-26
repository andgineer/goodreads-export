"""Library of ooks."""
import os
from pathlib import Path
from typing import Dict, Optional

from goodreads_export.author_file import AuthorFile
from goodreads_export.book_file import BookFile
from goodreads_export.data_file import ParseError
from goodreads_export.goodreads_book import Book, GoodreadsBooks
from goodreads_export.log import Log
from goodreads_export.series_file import SeriesFile
from goodreads_export.stat import Stat
from goodreads_export.templates import TemplateSet, TemplatesLoader

SUBFOLDERS = {
    "toread": "toread",  # for books without review and rating - supposedly this is from to-read
    "reviews": "reviews",  # all other books
    "authors": "authors",  # book authors
}

BOOKS_SUBFOLDERS = [SUBFOLDERS["reviews"], SUBFOLDERS["toread"]]


class Library:
    """Books and authors."""

    stat = Stat()

    def __init__(
        self,
        folder: Optional[Path] = None,
        log: Optional[Log] = None,
        templates: Optional[TemplateSet] = None,
    ) -> None:
        """Initialize.

        Without `folder` works in detached mode as base for file objects without ability to create files,
        just to access templates.
        """
        self.folder = folder
        self.log = log or Log()
        self.templates = templates or TemplatesLoader().load_builtin()

        self.books: Dict[str, BookFile] = {}
        self.authors: Dict[str, AuthorFile] = {}
        self.primary_authors: Dict[str, AuthorFile] = {}
        if folder is not None:
            self.authors = self.load_authors(folder / SUBFOLDERS["authors"])
            for books_subfolder in BOOKS_SUBFOLDERS:
                self.load_series(folder / books_subfolder, self.authors)
            for books_subfolder in BOOKS_SUBFOLDERS:
                self.books |= self.load_books(folder / books_subfolder, self.authors)

    def merge_author_names(self) -> None:
        """Replace all known versions of author names (translations, misspellings) with one primary name.

        All author name versions should be listed as links in one author file -
        just copy them from other author files to that `primary` author file.
        Fist name in the link will be used as primary name.

        Reviews will be relinked to the primary name.
        Author files with non-primary names will be deleted.
        Also recreate series files with primary author name in the file names.
        """
        for primary_author in [
            author
            for author in self.authors.values()
            if len(set(author.names) - {author.name}) > 0
        ]:
            for author_name in primary_author.names:
                if (
                    author_name in self.authors
                    and (author := self.authors[author_name]) != primary_author
                ):
                    self.log.debug(
                        f"Author {primary_author.name} has synonym {author.name} to merge"
                    )
                    self.stat.authors_renamed += 1
                    primary_author.merge(self.authors[author_name])
                    self.authors[author_name] = primary_author

    def dump(self, books: GoodreadsBooks) -> None:
        """Save `books` to the library files."""
        for subfolder in SUBFOLDERS.values():
            assert self.folder is not None  # for mypy
            os.makedirs(self.folder / subfolder, exist_ok=True)

        reviews_bar_title = "Review"
        authors_bar_title = "Author"
        self.log.open_progress(reviews_bar_title, "books", len(books))
        self.log.open_progress(authors_bar_title, "authors", bar_format="{desc}: {n_fmt}")

        for book in books:
            self.log.progress(reviews_bar_title)
            self.log.progress_description(reviews_bar_title, f"{book.title}")
            if self.stat.unique_author(book.author):
                self.log.progress(authors_bar_title)
            if book.author in self.authors and book.author != (
                primary_author := self.authors[book.author].name
            ):
                self.log.progress_description(
                    authors_bar_title, f"Author {book.author} changed to {primary_author}"
                )
                book.author = primary_author  # use the same author name for all synonyms

            if book.book_id not in self.books:
                if book.author not in self.authors:
                    self.authors[book.author] = self.create_author_file(book)
                    self.stat.authors_added += 1
                    self.log.progress_description(authors_bar_title, f"Added author {book.author}")
                added_file_path = self.create_book_file(book)
                # we know there was no file with this book ID so we added it for sure
                self.stat.books_added += 1
                self.log.debug(f"Added book {book.title}, {added_file_path} ")
        self.log.close_progress()

    def create_book_file(self, book: Book) -> str:
        """Create book file.

        Return the filename.
        """
        if book.review == "" and book.rating == 0:
            subfolder = SUBFOLDERS["toread"]
        else:
            subfolder = SUBFOLDERS["reviews"]
        assert self.folder is not None  # for mypy
        book_file = BookFile(
            library=self,
            title=book.title,
            folder=self.folder / subfolder,
            tags=book.tags,
            author=self.get_author(book.author),
            book_id=book.book_id,
            rating=book.rating,
            isbn=book.isbn,
            isbn13=book.isbn13,
            series_titles=book.series,
            review=book.review,
        )
        book_file.create_series_files()
        book_file.write()
        return os.path.join(subfolder, book_file.file_name)

    def create_author_file(self, book: Book) -> AuthorFile:
        """Create author file if id does not exist.

        Do not change already existed file.

        Return True if author file was added, False otherwise
        """
        assert self.folder is not None  # for mypy
        author_file = AuthorFile(
            library=self,
            name=book.author,
            folder=self.folder / SUBFOLDERS["authors"],
        )
        if not author_file.path.is_file():
            author_file.write()
        return author_file

    def get_author(self, name: str) -> AuthorFile:
        """Get author file."""
        if name not in self.authors:
            if self.folder is None:
                return AuthorFile(library=self, name=name)
            self.log.info(f"Creating author '{name}' ")
            self.authors[name] = AuthorFile(
                library=self, name=name, folder=self.folder / SUBFOLDERS["authors"]
            )
            self.authors[name].write()
        return self.authors[name]

    def load_series(self, folder: Path, authors: Dict[str, AuthorFile]) -> None:
        """Load existed series.

        Add them to authors.
        Could add series with the same title to the same author if they are in different files.
        """
        dummy_author = AuthorFile(library=Library(), name="author", folder=folder)
        dummy_series = SeriesFile(library=Library(), author=dummy_author, title="title")
        for file_name in folder.glob(f"*{dummy_series.file_name.suffix}"):
            if dummy_series.is_file_name(file_name):
                try:
                    series = SeriesFile(
                        library=self,
                        folder=folder,
                        file_name=Path(file_name.name),
                        content=file_name.read_text(encoding="utf8"),
                    )
                except ParseError:
                    self.log.info(f"Series file {file_name} has no author name")
                    continue
                if series.author.name not in authors:
                    self.log.info(f"Series file {file_name} has author without author file")
                    continue
                authors[series.author.name].series.append(series)
                self.stat.series_added += 1

    def load_books(self, folder: Path, authors: Dict[str, AuthorFile]) -> Dict[str, BookFile]:
        """Load existed books.

        Look for goodreads book ID inside files.
        Return {id: BookFile} for files with book ID, ignore other files.
        This way we ignore "- series" files and unknown files.
        """
        books: Dict[str, BookFile] = {}
        dummy_author = AuthorFile(library=Library(), name="author", folder=folder)
        dummy_book = BookFile(library=Library(), author=dummy_author, title="title")
        dummy_series = SeriesFile(library=Library(), author=dummy_author, title="title")
        for file_name in folder.glob(f"*{dummy_book.file_name.suffix}"):
            try:
                book = BookFile(  # also create author file if not yet existed
                    library=self,
                    folder=folder,
                    file_name=Path(file_name.name),
                    content=file_name.read_text(encoding="utf8"),
                )
                if book.book_id in books:
                    raise ValueError(
                        f"Duplicate book ID {book.book_id} in {file_name} "
                        f"and {books[book.book_id].file_name}"
                    )
                assert book.book_id is not None  # to please mypy
                books[book.book_id] = book
                authors[book.author.name].books.append(book)
            except ParseError:
                if not dummy_series.is_file_name(file_name):
                    self.stat.skipped_unknown_files += 1
        return books

    def load_authors(self, folder: Path) -> Dict[str, AuthorFile]:
        """Load existed authors.

        Return loaded authors
        """
        authors: Dict[str, AuthorFile] = {}
        dummy_author = AuthorFile(library=Library(), name="author", folder=folder)
        for file_name in folder.glob(f"*{dummy_author.file_name.suffix}"):
            author = AuthorFile(
                library=self,
                folder=folder,
                file_name=Path(file_name.name),
                name=file_name.stem,  # will be replaced by parsing file content
                content=file_name.read_text(encoding="utf8"),
            )
            if author.names:  # parse succeeded
                authors[author.name] = author  # primary name is always point to primary file
                for name in author.names:
                    if name not in authors:  # do not overwrite if pointed to primary file
                        authors[name] = author
            else:
                self.stat.skipped_unknown_files += 1
        return authors

    def check_templates(self) -> None:
        """Check templates and regexes."""
        author_name = "Jules Verne"
        book_id = "54479"
        title = "Around the World in Eighty Days"
        tags = ["#adventure", "#classics", "#fiction", "#novel", "#travel"]
        series_titles = ["Voyages extraordinaires"]
        review = "This is a review\nin two lines"
        author = AuthorFile(library=self, name=author_name)
        author.check()
        BookFile(
            library=self,
            book_id=book_id,
            title=title,
            author=author,
            tags=tags,
            series_titles=series_titles,
            review=review,
            rating=5,
        ).check()
        title = "title"
        SeriesFile(library=self, title=title, author=author).check()
