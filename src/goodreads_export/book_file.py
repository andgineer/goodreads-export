"""Book's file."""
import os
import re
import urllib.parse
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import jinja2

from goodreads_export.clean_file_name import clean_file_name
from goodreads_export.templates import ReviewTemplate, Templates


@dataclass
class BookFile:  # pylint: disable=too-many-instance-attributes
    """Book's markdown file.

    On init extract fields from `content` - override other parameters.
    To re-parse the `content` call `parse()`.
    `render()` generate `content` from fields.
    """

    template: ReviewTemplate
    title: str
    folder: Path
    content: Optional[str] = None
    file_name: Optional[Path] = None
    author: Optional[str] = None
    book_id: Optional[str] = None
    tags: Optional[List[str]] = None
    rating: Optional[int] = None
    isbn: Optional[int] = None
    isbn13: Optional[int] = None
    review: Optional[str] = None
    series: Optional[List[str]] = None

    _file_name: Optional[Path] = field(repr=False, init=False)
    _content: Optional[str] = field(repr=False, init=False)

    def __post_init__(self) -> None:
        """Extract fields from content."""
        self.jinja = jinja2.Environment()
        self.jinja_context: Dict[str, Any] = {
            "book": self,
            "urlencode": urllib.parse.urlencode,
            "clean_file_name": clean_file_name,
        }
        self.parse()  # we do not run parse on content assign during __init__()
        if self.tags is None:
            self.tags = []
        if self.series is None:
            self.series = []

    def parse(self) -> None:
        """Parse markdown file content."""
        if self._content is not None:
            self.book_id = None
            self.title = ""
            self.author = None
            self.series = []
            if book_regex := self.template.goodreads_link_regexes.choose_regex(self._content):
                link_match = book_regex.compiled.search(self._content)
                assert link_match is not None  # to please mypy
                self.book_id = link_match[book_regex.book_id_group]
                self.title = link_match[book_regex.title_group]
                self.author = link_match[book_regex.author_group]
            if series_regex := self.template.series_regexes.choose_regex(self._content):
                self.series = [
                    series_match[series_regex.series_group]
                    for series_match in series_regex.compiled.finditer(self._content)
                ]

    def render_body(self) -> Optional[str]:
        """Render file body."""
        assert self.tags is not None  # to please mypy
        if "#book/book" not in self.tags:
            self.tags.append("#book/book")
        if self.rating is not None and self.rating > 0:
            rating_tag = f"#book/rating{self.rating}"
            if rating_tag not in self.tags:
                self.tags.append(rating_tag)
        return self.template.render_body(self.jinja_context)

    def series_full_name(self, series: str) -> str:
        """Return file name without extension for series."""
        assert self.author is not None
        return clean_file_name(f"{self.author} - {series} - series")  # todo replace with template

    def is_series_file_name(self) -> bool:
        """Return True if file name if indicate this is series description file."""
        assert self.file_name is not None
        return (
            re.match(r".* - .* - series\.md$", str(self.file_name)) is not None
        )  # todo replace with template

    def series_file_name(self, series: str) -> Path:
        """Return file name for series."""
        context = self.jinja_context.copy()
        context["series"] = series
        return self.template.series.render_file_name(context)

    @property  # type: ignore
    def file_name(self) -> Optional[Path]:
        """Markdown file name.

        Automatically generate file name from book's fields if not assigned.
        """
        if self._file_name is None:
            self._file_name = self.template.render_file_name(self.jinja_context)
        return self._file_name

    @file_name.setter
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
        """Markdown file content.

        Automatically generate content from book's fields if not assigned.
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

    def series_list_full_names(self) -> Dict[str, str]:
        """Return dict of series full names."""
        assert self.series is not None  # to please mypy
        return {series: self.series_full_name(series) for series in self.series}

    def delete_series_files(self) -> Dict[str, Path]:
        """Delete series files for review.

        Return deleted series files {series name: series file path}
        """
        deleted_series_files = {}
        assert self.series is not None
        for series in self.series:
            series_file_path = self.folder / self.series_file_name(series)
            if series_file_path.exists():
                os.remove(series_file_path)
                deleted_series_files[series] = series_file_path
        return deleted_series_files

    def rename_author(self, new_author: str) -> Tuple[Dict[str, Path], Dict[str, Path]]:
        """Rename author in review file.

        In content replace links only, do not re-render content to keep user changes.
        Also recreate series files with new author name in the file names.

        Return (deleted series files, created series files)
        """
        assert self.author is not None
        assert self.content is not None
        old_series_names = self.series_list_full_names()
        deleted_series_files = self.delete_series_files()
        self.delete_file()
        self.content = self.content.replace(f"[[{self.author}]]", f"[[{new_author}]]")
        self.author = new_author
        self._file_name = None  # to recreate from fields
        for series_name, series_full in old_series_names.items():
            self.content = self.content.replace(series_full, self.series_full_name(series_name))
        created_series_files = self.create_series_files()
        self.write()
        return deleted_series_files, created_series_files

    def create_series_files(self) -> Dict[str, Path]:
        """Create series files if they do not exist.

        Do not change already existed files.
        Return created series files {series name: series file path}
        """
        assert self.series is not None
        assert self.author is not None
        created_series_files = {}
        for series in self.series:
            series_file_name = self.series_file_name(series)
            series_file_path = self.folder / series_file_name
            if not series_file_path.is_file():
                with series_file_path.open("w", encoding="utf8") as md_file:
                    context = self.jinja_context.copy()
                    context["series"] = series
                    md_file.write(self.template.series.render_body(context))
                created_series_files[series] = series_file_path
        return created_series_files

    @classmethod
    def check(cls) -> bool:
        """Check regexps for the template."""
        author = "Jules Verne"
        book_id = "54479"
        title = "Around the World in Eighty Days"
        tags = ["adventure", "classics", "fiction", "novel", "travel"]
        series = ["Voyages extraordinaires"]
        review = "This is a review\nin two lines"
        book_file = cls(
            template=Templates().review,
            book_id=book_id,
            title=title,
            folder=Path(),
            author=author,
            tags=tags,
            series=series,
            review=review,
            rating=5,
        )
        book_file.content = book_file.render_body()
        is_book_id_parsed = book_file.book_id == book_id
        is_title_parsed = book_file.title == title
        is_author_parsed = book_file.author == author
        is_series_parsed = book_file.series == series
        # todo detailed error diagnostics like in AuthorFile
        return is_book_id_parsed and is_title_parsed and is_author_parsed and is_series_parsed
