"""Create files for books."""
import os
from pathlib import Path
from typing import Dict, Tuple

from goodreads_export.author_file import AuthorFile
from goodreads_export.book_file import BookFile
from goodreads_export.goodreads_book import Book, GoodreadsBooks
from goodreads_export.log import Log
from goodreads_export.series_file import SeriesFile
from goodreads_export.stat import Stat

SUBFOLDERS = {
    "toread": "toread",  # for books without review and rating - supposedly this is from to-read
    "reviews": "reviews",  # all other books
    "authors": "authors",  # book authors
}

BOOKS_SUBFOLDERS = [SUBFOLDERS["reviews"], SUBFOLDERS["toread"]]


class BooksFolder:
    """Create files for books and authors."""

    stat = Stat()

    def __init__(self, folder: Path, log: Log) -> None:
        """Initialize."""
        self.folder = folder
        self.log = log

        self.books: Dict[str, BookFile] = {}
        self.authors: Dict[str, AuthorFile] = {}
        self.primary_authors: Dict[str, AuthorFile] = {}
        self.authors, self.primary_authors = self.load_authors(folder / SUBFOLDERS["authors"])
        for books_subfolder in BOOKS_SUBFOLDERS:
            self.load_series(folder / books_subfolder, self.authors)
        for books_subfolder in BOOKS_SUBFOLDERS:
            self.books |= self.load_books(folder / books_subfolder, self.authors)

    def merge_author_names(self) -> None:
        """Replace all known versions of author names (translations, misspellings) with one primary name.

        All author name versions should be listed as links in one author file -
        just copy them from other author files to that `primary` author file.
        Reviews will be relinked to this file.
        Author files of this author with one name in them will be deleted.
        Also recreate series files with new author name in the file names.
        """
        # todo for author: if names then merge with other AuthorFiles and delete them
        for primary_author in self.primary_authors.values():
            for author_name in primary_author.names:
                if (
                    author_name in self.authors
                    and (author := self.authors[author_name]) != primary_author
                ):
                    self.log.debug(
                        f"Author {primary_author.name} has synonim {author.name} to merge"
                    )
                    # primary_author.merge(self.authors[author_name])
                    self.authors[author_name] = primary_author
                    self.stat.author_removed_names += author.name
        for book in self.books.values():
            if book.author in self.authors and book.author != self.authors[book.author].name:
                self.log.debug(  # should be before rename to log old author name
                    f"Modified review {book.file_name}: renamed author {book.author}"
                    f" to {self.authors[book.author].name}"
                )
                deleted_series_files, created_series_files = book.rename_author(
                    self.authors[book.author].name  # type: ignore
                )
                self.log.debug(
                    f"Deleted series files: {[str(path) for path in deleted_series_files.values()]}, "
                    f"created: {[str(path) for path in created_series_files.values()]}."
                )
                self.stat.authors_renamed += 1
        # for author_name in self.primary_authors.values():
        #     removed_names = author_name.remove_non_primary_files()
        #     self.log.debug(f"Removed {author_name.name}'s duplicate names: {removed_names}")
        #     self.stat.author_removed_names += removed_names

    def dump(self, books: GoodreadsBooks) -> None:
        """Save books and authors as md-files."""
        for subfolder in SUBFOLDERS.values():
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
                if book.author not in self.authors and self.create_author_file(book):
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
        book_file = BookFile(
            title=book.title,
            folder=self.folder / subfolder,
            tags=book.tags,
            author=self.authors[book.author].name if book.author in self.authors else book.author,
            book_id=book.book_id,
            rating=book.rating,
            isbn=book.isbn,
            isbn13=book.isbn13,
            series_titles=book.series,
            review=book.review,
        )
        book_file.create_series_files()
        book_file.write()
        assert book_file.file_name is not None  # to make mypy happy
        return os.path.join(subfolder, book_file.file_name)

    def create_author_file(self, book: Book) -> bool:
        """Create author file if id does not exist.

        Do not change already existed file.

        Return True if author file was added, False otherwise
        """
        author_file = AuthorFile(
            name=book.author,
            folder=self.folder / SUBFOLDERS["authors"],
        )
        assert author_file.file_name is not None  # to make mypy happy
        if not (author_file.folder / author_file.file_name).is_file():
            author_file.write()
            return True
        return False

    def load_series(self, folder: Path, authors: Dict[str, AuthorFile]) -> None:
        """Load existed series.

        Add them to authors.
        Could add series with the same title to the same author if they are in different files.
        """
        for file_name in folder.glob(f"*{SeriesFile.file_suffix()}"):
            if SeriesFile.is_file_name(file_name):
                series = SeriesFile(
                    folder=folder,
                    file_name=Path(file_name.name),
                    content=file_name.read_text(encoding="utf8"),
                )
                if series.author is None:
                    self.log.info(f"Series file {file_name} has no author name")
                    self.stat.skipped_unknown_files += 1
                    continue
                if series.author not in authors:
                    self.log.info(f"Series file {file_name} has author without author file")
                    self.stat.skipped_unknown_files += 1
                    continue
                authors[series.author].series.append(series)
                self.stat.series_added += 1

    def load_books(self, folder: Path, authors: Dict[str, AuthorFile]) -> Dict[str, BookFile]:
        """Load existed books.

        Look for goodreads book ID inside files.
        Return {id: BookFile} for files with book ID, ignore other files.
        This way we ignore "- series" files and unknown files.
        """
        # todo also add to authors for ease of merge
        books: Dict[str, BookFile] = {}
        for file_name in folder.glob(f"*{BookFile.file_suffix()}"):
            book = BookFile(
                folder=folder,
                file_name=Path(file_name.name),
                content=file_name.read_text(encoding="utf8"),
            )
            if book.book_id is None:
                if SeriesFile.file_suffix != BookFile.file_suffix or not SeriesFile.is_file_name(
                    file_name
                ):
                    self.stat.skipped_unknown_files += 1
            elif book.book_id in books:
                raise ValueError(
                    f"Duplicate book ID {book.book_id} in {file_name} "
                    f"and {books[book.book_id].file_name}"
                )
            else:
                books[book.book_id] = book
                if book.author not in authors:
                    self.log.info(
                        f"Book file {file_name} has author '{book.author}' without author file"
                    )
                    continue
                authors[book.author].books.append(book)
        return books

    def load_authors(self, folder: Path) -> Tuple[Dict[str, AuthorFile], Dict[str, AuthorFile]]:
        """Load existed authors.

        Primary authors - author with list of more than one name inside the file
        Return (all-authors, primary-authors)
        all-authors names could point to the same multi-name file if no primary file found for this name
        """
        authors: Dict[str, AuthorFile] = {}
        primary_authors: Dict[str, AuthorFile] = {}
        dummy_author = AuthorFile(name="author", folder=folder)
        for file_name in folder.glob(f"*{dummy_author.file_name.suffix}"):  # type: ignore
            author = AuthorFile(
                folder=folder,
                file_name=Path(file_name.name),
                name=file_name.stem,  # will be replaced by parsing file content
                content=file_name.read_text(encoding="utf8"),
            )
            if author.names:  # parse succeeded
                is_primary_file = len(set(author.names) - {author.name}) > 0
                if is_primary_file:
                    primary_authors[author.name] = author

                authors[author.name] = author  # primary name is always point to primary file
                for name in author.names:
                    if name not in authors:  # do not overwrite if pointed to primary file
                        authors[name] = author
            else:
                self.stat.skipped_unknown_files += 1
        return authors, primary_authors
