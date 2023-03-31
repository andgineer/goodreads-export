"""Book's object."""
import os
import urllib.parse
from pathlib import Path
from typing import Any, Dict, List, Optional

from goodreads_export.authored_file import AuthoredFile
from goodreads_export.data_file import ParseError
from goodreads_export.series_file import SeriesFile
from goodreads_export.templates import BookTemplate


class BookFile(AuthoredFile):  # pylint: disable=too-many-instance-attributes
    """Book's object.

    On init extract fields from `content` - override other parameters.
    To re-parse the `content` call `parse()`.
    `render()` generate `content` from fields.
    """

    title: Optional[str]
    book_id: Optional[str]
    tags: List[str]
    rating: Optional[int]
    isbn: Optional[int]
    isbn13: Optional[int]
    review: Optional[str]
    series_titles: List[str]

    def __init__(  # pylint: disable=too-many-arguments
        self,
        *,
        title: Optional[str] = None,
        book_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        rating: Optional[int] = None,
        isbn: Optional[int] = None,
        isbn13: Optional[int] = None,
        review: Optional[str] = None,
        series_titles: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> None:
        """Init."""
        super().__init__(**kwargs)
        self.title = title
        self.book_id = book_id
        self.tags = tags or []
        self.rating = rating
        self.isbn = isbn
        self.isbn13 = isbn13
        self.review = review
        self.series_titles = series_titles or []
        self.parse()

    def _get_template(self) -> BookTemplate:
        """Template."""
        return self.library.templates.book

    def _get_template_context(self) -> Dict[str, Any]:
        """Template context."""
        return {
            "book": self,
            "author": self.author,
            "urlencode": urllib.parse.urlencode,
        }

    def parse(self) -> None:
        """Parse file content."""
        if self._content is None:
            return
        self.series_titles = []
        if book_regex := self._get_template().goodreads_link_regexes.choose_regex(self._content):
            link_match = book_regex.compiled.search(self._content)
            assert link_match is not None  # to please mypy
            self.book_id = link_match[book_regex.book_id_group]
            self.title = link_match[book_regex.title_group]
            self.author = self.library.get_author(link_match[book_regex.author_group])
        else:
            raise ParseError(
                f"Cannot extract book information from file content:\n{self._content}"
            )
        if series_regex := self._get_template().series_regexes.choose_regex(self._content):
            self.series_titles = [
                series_match[series_regex.series_group]
                for series_match in series_regex.compiled.finditer(self._content)
            ]

    def render_body(self) -> str:
        """Render file body."""
        assert self.tags is not None  # to please mypy
        if "#book/book" not in self.tags:
            self.tags.append("#book/book")
        if self.rating is not None and self.rating > 0:
            rating_tag = f"#book/rating{self.rating}"
            if rating_tag not in self.tags:
                self.tags.append(rating_tag)
        return self._get_template().render_body(self._get_template_context())

    def write(self) -> None:
        """Write markdown file to path.

        If the file with `author - title.md` already exists, append book ID to the file name.
        Even if this file also exists that does not matter because this it the book
        with the same ID.
        """
        assert self.folder is not None  # to please mypy
        assert self.book_id is not None  # to please mypy
        if (self.folder / self.file_name).exists() and self.book_id not in str(self.file_name):
            self.file_name = Path(
                f"{self.file_name.with_suffix('')} - {self.book_id}{self.file_name.suffix}"
            )
        super().write()

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

    def create_series_files(self) -> Dict[str, Path]:
        """Create series files if they do not exist.

        Do not change already existed files.
        Return created series files {series name: series file path}
        """
        created_series_files = {}
        for series in self.series:
            if not series.path.is_file():
                assert series.title is not None  # to please mypy
                series.write()
                created_series_files[series.title] = series.path
        return created_series_files

    def check(self) -> bool:
        """Check regexps for the template.

        Create file from fields and after that parse it and compare parsed values with the initial fields
        """
        book_id = self.book_id
        title = self.title
        author_name = self.author.name
        series_titles = self.series_titles
        self.content = self.render_body()
        is_book_id_parsed = self.book_id == book_id
        is_title_parsed = self.title == title
        is_author_parsed = self.author.name == author_name
        is_series_parsed = self.series_titles == series_titles
        if not is_author_parsed:
            print(f"Author name {author_name} is not parsed from content\n{self.content}")
            print(f"using the pattern\n{self._get_template().goodreads_link_regexes[0].regex}")
        if not is_book_id_parsed:
            print(f"Book ID {book_id} is not parsed from content\n{self.content}")
            print(f"using the pattern\n{self._get_template().goodreads_link_regexes[0].regex}")
        if not is_title_parsed:
            print(f"Book title {title} is not parsed from content\n{self.content}")
            print(f"using the pattern\n{self._get_template().goodreads_link_regexes[0].regex}")
        if not is_series_parsed:
            print(f"Series {series_titles[0]} is not parsed from content\n{self.content}")
            print(f"using the pattern\n{self._get_template().series_regexes[0].regex}")
        return is_book_id_parsed and is_title_parsed and is_author_parsed and is_series_parsed

    @property
    def series(self) -> List[SeriesFile]:
        """List of series objects constructed from series_names."""
        return [
            SeriesFile(library=self.library, folder=self.folder, title=title, author=self.author)
            for title in self.series_titles
        ]
