"""Book's file."""
import os
import re
import urllib.parse
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from goodreads_export.clean_file_name import clean_file_name


@dataclass
class BookFile:  # pylint: disable=too-many-instance-attributes
    """Book's markdown file.

    On init extract fields from `content` - override other parameters.
    To re-parse the `content` call `parse()`.
    `render()` generate `content` from fields.
    """

    title: str
    content: Optional[str] = None
    folder: Optional[Path] = None
    file_name: Optional[str] = None
    author: Optional[str] = None
    book_id: Optional[str] = None
    tags: Optional[List[str]] = None
    rating: Optional[int] = None
    isbn: Optional[int] = None
    isbn13: Optional[int] = None
    review: Optional[int] = None
    series: Optional[List[str]] = None

    _file_name: Optional[str] = field(repr=False, init=False)
    _goodreads_link_pattern: re.Pattern[str] = field(
        repr=False,
        init=False,
        default=re.compile(
            r"\[\[([^]]+)\]\](: \[([^]]*)\]\(https://www\.goodreads\.com/book/show/(\d+)\))"
        ),
    )
    _series_link_pattern: re.Pattern[str] = field(
        repr=False,
        init=False,
        default=re.compile(r"\[\[[^-]* - ([^-]*) - series\]\]"),
    )

    def __post_init__(self) -> None:
        """Extract fields from content."""
        self.parse()  # we do not run parse on content assign during __init__()
        if self.content is None:
            self.render()
        if self.tags is None:
            self.tags = []
        if self.series is None:
            self.series = []

    def parse(self) -> None:
        """Parse markdown file content."""
        if self.content is not None:
            if (series_match := self._goodreads_link_pattern.search(self.content)) is not None:
                self.book_id = series_match[4]
                self.title = series_match[3]
                self.author = series_match[1]

            self.series = [
                series_match[1]
                for series_match in self._series_link_pattern.finditer(self.content)
            ]

    def render(self) -> None:
        """Render markdown file content."""
        required = ["book_id", "title", "author", "tags", "series", "review", "rating"]
        for attribute in required:
            if getattr(self, attribute) is None:
                raise ValueError(f"To create review file need attribute '{attribute}'")
        assert self.tags is not None  # to please mypy
        assert self.author is not None  # to please mypy
        assert self.series is not None  # to please mypy
        if "#book/book" not in self.tags:
            self.tags.append("#book/book")
        if self.rating is not None and self.rating > 0:
            rating_tag = f"#book/rating{self.rating}"
            if rating_tag not in self.tags:
                self.tags.append(rating_tag)
        book_url = f"https://www.goodreads.com/book/show/{self.book_id}"
        self.content = f"""
[[{clean_file_name(self.author)}]]: [{self.title}]({book_url})
ISBN{self.isbn} (ISBN13{self.isbn13})
{' '.join(['[[' + self.series_full_name(series) + ']]' for series in self.series])}
{self.review}

[Search in Calibre](calibre://search/_?q={urllib.parse.quote(self.title)})

{" ".join(self.tags)}
"""

    @property  # type: ignore
    def file_name(self) -> str:
        """Markdown file name.

        Automatically generate file name from book's fields if not assigned.
        """
        if self._file_name is None:
            assert self.title is not None
            assert self.author is not None
            self._file_name = f"{clean_file_name(self.author)} - {clean_file_name(self.title)}.md"
        return self._file_name

    def series_full_name(self, series: str) -> str:
        """Return file name without extension for series."""
        assert self.author is not None
        return clean_file_name(f"{self.author} - {series} - series")

    def series_file_name(self, series: str) -> str:
        """Return file name for series."""
        return f"{self.series_full_name(series)}.md"

    @file_name.setter  # type: ignore  # same name as property
    def file_name(self, file_name: str) -> None:
        """Set file_name.

        Set None by default (if not in __init__() params)
        """
        if isinstance(file_name, property):
            self._file_name = None
            return
        self._file_name = file_name

    def write(self) -> None:
        """Write markdown file to path."""
        assert self.file_name is not None  # to please mypy
        assert self.content is not None  # to please mypy
        assert self.folder is not None  # to please mypy
        with (self.folder / self.file_name).open("w", encoding="utf8") as file:
            file.write(self.content)

    def delete_file(self) -> None:
        """Delete the book file."""
        assert (
            self.folder is not None and self.file_name is not None
        ), "Can not delete file without folder"
        if (self.folder / self.file_name).exists():
            os.remove(self.folder / self.file_name)

    def delete_series_files(self) -> Dict[str, str]:
        """Delete series files for review.

        Return deleted series {series name: series link}
        """
        old_series_names = {}
        assert self.series is not None
        assert self.folder is not None, "Can not delete series without folder"
        for series in self.series:
            old_series_names[series] = self.series_full_name(series)
            series_file_name = self.series_file_name(series)
            if (self.folder / series_file_name).exists():
                os.remove(self.folder / series_file_name)
        return old_series_names

    def rename_author(self, new_author: str) -> None:
        """Rename author in review file.

        In content replace links only, do not re-render content to keep user changes
        """
        assert self.author is not None
        assert self.content is not None
        old_series_names = self.delete_series_files()
        self.delete_file()
        self.content = self.content.replace(f"[[{self.author}]]", f"[[{new_author}]]")
        self.author = new_author
        self._file_name = None  # to recreate from fields
        for series_name, series_full in old_series_names.items():
            self.content = self.content.replace(series_full, self.series_full_name(series_name))
        self.create_series_files()
        self.write()

    def create_series_files(self) -> None:
        """Create series files if they do not exist.

        Do not change already existed files.
        """
        assert self.series is not None
        assert self.author is not None
        assert self.folder is not None, "Can not create series without folder"
        for series_idx, series in enumerate(self.series):
            series_file_name = self.series_file_name(series)
            search_params = urllib.parse.urlencode(
                {
                    "utf8": "✓",
                    "q": f"{self.series[series_idx]}, #",
                    "search_type": "books",
                    "search[field]": "title",
                }
            )
            series_file_path = self.folder / series_file_name
            if not series_file_path.is_file():
                with series_file_path.open("w", encoding="utf8") as md_file:
                    md_file.write(
                        f"""[[{clean_file_name(self.author)}]]
[{self.series[series_idx]}](https://www.goodreads.com/search?{search_params})"""
                    )
