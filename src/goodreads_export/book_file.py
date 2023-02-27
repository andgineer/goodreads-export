"""Book's file."""
import os
import urllib.parse
from dataclasses import dataclass, field
from functools import cache
from pathlib import Path
from typing import Any, Dict, List, Optional

from goodreads_export.clean_file_name import clean_file_name
from goodreads_export.data_file import DataFile
from goodreads_export.series_file import SeriesFile
from goodreads_export.templates import get_templates


@dataclass(eq=False)
class BookFile(DataFile):  # pylint: disable=too-many-instance-attributes
    """Book's markdown file.

    On init extract fields from `content` - override other parameters.
    To re-parse the `content` call `parse()`.
    `render()` generate `content` from fields.
    """

    title: Optional[str] = None
    folder: Optional[Path] = Path()
    author: Optional[str] = None
    content: Optional[str] = field(default=None, repr=False)
    file_name: Optional[Path] = field(default=None, repr=False)
    book_id: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    rating: Optional[int] = None
    isbn: Optional[int] = None
    isbn13: Optional[int] = None
    review: Optional[str] = None
    series_titles: List[str] = field(default_factory=list)

    _file_name: Optional[Path] = field(init=False)
    _content: Optional[str] = field(init=False)

    def __post_init__(self) -> None:
        """Extract fields from content."""
        self._template = get_templates().book
        self.parse()  # we do not run parse on content assign during __init__()

    @cache  # pylint: disable=method-cache-max-size-none
    def _template_context(self) -> Dict[str, Any]:
        """Template context."""
        return {
            "book": self,
            "author": self.author,
            "urlencode": urllib.parse.urlencode,
            "clean_file_name": clean_file_name,
        }

    def parse(self) -> None:
        """Parse file content."""
        if self._content is None:
            return
        self.book_id = None
        self.title = None
        self.author = None
        self.series_titles = []
        if book_regex := get_templates().book.goodreads_link_regexes.choose_regex(self._content):
            link_match = book_regex.compiled.search(self._content)
            assert link_match is not None  # to please mypy
            self.book_id = link_match[book_regex.book_id_group]
            self.title = link_match[book_regex.title_group]
            self.author = link_match[book_regex.author_group]
        if series_regex := get_templates().book.series_regexes.choose_regex(self._content):
            self.series_titles = [
                series_match[series_regex.series_group]
                for series_match in series_regex.compiled.finditer(self._content)
            ]

    @cache  # pylint: disable=method-cache-max-size-none
    def render_body(self) -> Optional[str]:
        """Render file body."""
        assert self.tags is not None  # to please mypy
        if "#book/book" not in self.tags:
            self.tags.append("#book/book")
        if self.rating is not None and self.rating > 0:
            rating_tag = f"#book/rating{self.rating}"
            if rating_tag not in self.tags:
                self.tags.append(rating_tag)
        return get_templates().book.render_body(self._template_context())

    @property  # type: ignore
    def file_name(self) -> Optional[Path]:
        """Markdown file name.

        Automatically generate file name from book's fields if not assigned.
        """
        if self._file_name is None:
            self._file_name = get_templates().book.render_file_name(self._template_context())
        return self._file_name

    @classmethod
    @cache
    def file_suffix(cls) -> str:
        """File suffix."""
        file_name = BookFile(title="title", author="author").file_name
        assert file_name
        return file_name.suffix

    @file_name.setter  # type: ignore
    def file_name(self, file_name: Path) -> None:
        """Set file_name.

        Set None by default (if not in __init__() params)
        """
        if isinstance(file_name, property):
            self._file_name = None
            return
        self._file_name = file_name

    @property  # type: ignore  # same name as property
    def content(self) -> Optional[str]:
        """File content.

        Automatically generate content from object's fields if not assigned.
        """
        if self._content is None:
            self._content = self.render_body()
        return self._content

    @content.setter
    def content(self, content: str) -> None:
        """Set content.

        Set None by default (if not in __init__() params)
        """
        if isinstance(content, property):
            self._content = None
            return
        self._content = content
        self.parse()

    def write(self) -> None:
        """Write markdown file to path.

        If the file with `author - title.md` already exists, append book ID to the file name.
        Even if this file also exists that does not matter because this it the book
        with the same ID.
        """
        assert self.file_name is not None  # to please mypy
        assert self.content is not None  # to please mypy
        assert self.folder is not None  # to please mypy
        if (
            (self.folder / self.file_name).exists()
            and self.book_id is not None
            and self.book_id not in str(self.file_name)
        ):
            self.file_name = Path(
                f"{self.file_name.with_suffix('')} - {self.book_id}{self.file_name.suffix}"
            )
        with (self.folder / self.file_name).open("w", encoding="utf8") as file:
            file.write(self.content)

    def delete_file(self) -> None:
        """Delete the book file."""
        assert (
            self.folder is not None and self.file_name is not None
        ), "Can not delete file without folder"
        if (self.folder / self.file_name).exists():
            os.remove(self.folder / self.file_name)

    def delete_series_files(self) -> Dict[str, Path]:
        """Delete series files for review.

        Return deleted series files {series name: series file path}
        """
        deleted_series_files = {}
        assert self.series_titles is not None
        for series in self.series_titles:
            series_file_path = self.folder / self.series_file_name(series)  # type: ignore  # pylint: disable=no-member
            if series_file_path.exists():
                os.remove(series_file_path)
                deleted_series_files[series] = series_file_path
        return deleted_series_files

    def rename_author(self, new_author: str) -> None:
        """Rename author in book file.

        In content replace author name only, do not re-render content to keep possible user changes intact.
        """
        self.delete_file()
        assert self.author is not None  # to please mypy
        old_author_name = self.author
        self.author = new_author
        self._file_name = None  # to force re-rendering
        assert self.content is not None  # to please mypy
        self.content = self.content.replace(old_author_name, new_author)
        self.write()

    def create_series_files(self) -> Dict[str, Path]:
        """Create series files if they do not exist.

        Do not change already existed files.
        Return created series files {series name: series file path}
        """
        # todo in perfect world we create series from author
        assert self.series_titles is not None
        assert self.author is not None
        created_series_files = {}
        for series in self.series:
            if not series.path.is_file():
                assert series.title is not None  # to please mypy
                series.write()
                created_series_files[series.title] = series.path
        return created_series_files

    @classmethod
    def check(cls) -> bool:
        """Check regexps for the template."""
        author = "Jules Verne"
        book_id = "54479"
        title = "Around the World in Eighty Days"
        tags = ["#adventure", "#classics", "#fiction", "#novel", "#travel"]
        series_titles = ["Voyages extraordinaires"]
        review = "This is a review\nin two lines"
        book_file = cls(
            folder=Path(),
            book_id=book_id,
            title=title,
            author=author,
            tags=tags,
            series_titles=series_titles,
            review=review,
            rating=5,
        )
        book_file.content = book_file.render_body()
        is_book_id_parsed = book_file.book_id == book_id
        is_title_parsed = book_file.title == title
        is_author_parsed = book_file.author == author
        is_series_parsed = book_file.series_titles == series_titles
        # assert book_file.series == ['']
        if not is_author_parsed:
            print(f"Author name {author} is not parsed from content\n{book_file.content}")
            print(f"using the pattern\n{get_templates().book.goodreads_link_regexes[0].regex}")
        if not is_book_id_parsed:
            print(f"Book ID {book_id} is not parsed from content\n{book_file.content}")
            print(f"using the pattern\n{get_templates().book.goodreads_link_regexes[0].regex}")
        if not is_title_parsed:
            print(f"Book title {title} is not parsed from content\n{book_file.content}")
            print(f"using the pattern\n{get_templates().book.goodreads_link_regexes[0].regex}")
        if not is_series_parsed:
            print(f"Series {series_titles[0]} is not parsed from content\n{book_file.content}")
            print(f"using the pattern\n{get_templates().book.series_regexes[0].regex}")
        return is_book_id_parsed and is_title_parsed and is_author_parsed and is_series_parsed

    @property
    # @cache
    def series(self) -> List[SeriesFile]:
        """List of series objects constructed from series_names."""
        return [
            SeriesFile(folder=self.folder, title=title, author=self.author)
            for title in self.series_titles
        ]

    def __hash__(self) -> int:
        """Dataclass set it to None as it is not frozen."""
        return hash(self.__repr__())
