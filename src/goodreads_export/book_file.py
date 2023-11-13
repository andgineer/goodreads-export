"""Book's object."""
import urllib.parse
from pathlib import Path
from typing import Any, Dict, List, Optional

from goodreads_export.authored_file import AuthoredFile
from goodreads_export.data_file import ParseError
from goodreads_export.series_file import SeriesFile
from goodreads_export.templates import BookTemplate


class BookFile(AuthoredFile):  # pylint: disable=too-many-instance-attributes
    """Book's object."""

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
        """Set fields from args. Rewrite them from content if provided."""
        self.title = title
        self.book_id = book_id
        self.tags = tags or []
        self.rating = rating
        self.isbn = isbn
        self.isbn13 = isbn13
        self.review = review
        self.series_titles = series_titles or []
        super().__init__(**kwargs)

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
        assert self._content is not None, "Cannot parse None content"
        self.series_titles = []
        if book_regex := self._get_template().goodreads_link_regexes.choose_regex(self._content):
            link_match = book_regex.compiled.search(self._content)
            assert link_match is not None, (
                "impossible happened: after successful `search` in "
                "`choose_regex` got `None` for search with same params"
            )
            self.book_id = link_match[book_regex.book_id_group]
            self.title = link_match[book_regex.title_group]
            self.author = self.library.author_factory(link_match[book_regex.author_group])
        else:
            raise ParseError(
                f"Cannot extract book information from file content:\n{self._content}"
            )
        if series_regex := self._get_template().series_regexes.choose_regex(self._content):
            self.series_titles = [
                series_match[series_regex.series_group]
                for series_match in series_regex.compiled.finditer(self._content)
            ]

    def write(self) -> None:
        """Write markdown file to path.

        If the file with `author - title.md` already exists, append book ID to the file name.
        Even if this file also exists that does not matter because that should be the book
        with the same ID.
        """
        assert self.folder is not None, "Cannot write to None folder"
        assert self.book_id is not None, "Cannot write book not knowing its ID"
        if (self.folder / self.file_name).exists() and self.book_id not in str(self.file_name):
            self.file_name = Path(
                f"{self.file_name.with_suffix('')} - {self.book_id}{self.file_name.suffix}"
            )
        super().write()

    def create_series_files(self) -> Dict[str, Path]:
        """Create series files if they do not exist.

        Do not change already existed files.
        Return created series files {series name: series file path}
        """
        created_series_files = {}
        for series in self.series:
            if not series.path.is_file():
                series.write()
                created_series_files[series.title] = series.path
        return created_series_files

    def check(self) -> bool:
        """Check regexps for the template.

        Create file from fields and after that parse it and compare parsed values
        with the initial fields
        """
        return self.check_regexes(
            {
                "Book ID": {"value": lambda: self.book_id},
                "Book title": {"value": lambda: self.title},
                "Author name": {"value": lambda: self.author.name},
                "Series": {
                    "value": lambda: self.series_titles,
                    "regex": self._get_template().series_regexes[0].regex,
                },
            },
            self._get_template().goodreads_link_regexes[0].regex,
        )

    @property
    def series(self) -> List[SeriesFile]:
        """List of series objects constructed from series_names."""
        return [
            SeriesFile(library=self.library, folder=self.folder, title=title, author=self.author)
            for title in self.series_titles
        ]
