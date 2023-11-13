"""Author's object."""
import urllib.parse
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Optional

from goodreads_export.data_file import DataFile, ParseError
from goodreads_export.series_file import SeriesList
from goodreads_export.templates import AuthorTemplate

if TYPE_CHECKING:
    from goodreads_export.book_file import BookFile


class AuthorFile(DataFile):
    """Author's object."""

    name: str  # primary author name
    names: list[str]
    series: SeriesList
    books: list["BookFile"]

    def __init__(
        self,
        *,
        name: str,
        names: Optional[list[str]] = None,
        series: Optional[SeriesList] = None,
        books: Optional[list["BookFile"]] = None,
        **kwargs: Any,
    ) -> None:
        """Set fields from args. Rewrite them from content if provided."""
        self.name = name
        self.names = names if names is not None else [name]
        assert name in self.names, f"Primary name '{name}' must be in names {self.names}"
        self.series = series or SeriesList()
        self.books = books or []
        super().__init__(**kwargs)

    def _get_template(self) -> AuthorTemplate:
        """Template."""
        return self.library.templates.author

    def _get_template_context(self) -> Dict[str, Any]:
        """Template context."""
        return {
            "author": self,
            "urlencode": urllib.parse.urlencode,
        }

    def parse(self) -> None:
        """Parse file content."""
        assert self._content is not None, "Cannot parse None content"
        self.names = []
        if regex := self._get_template().names_regexes.choose_regex(self._content):
            self.names = [
                match[regex.name_group] for match in regex.compiled.finditer(self._content)
            ]
            self.name = self.names[0]  # first name is primary
        else:
            raise ParseError(
                f"Cannot extract author information from file content:\n{self._content}"
            )

    def merge(self, other: "AuthorFile") -> None:
        """Merge `other` author with this one."""
        for book in other.books:
            book.rename_author(self.name)
        for series in other.series:
            series.rename_author(self.name)
        self.books += other.books
        self.series += other.series
        other.delete_file()

    def delete_series(self) -> Dict[str, Path]:
        """Delete series and their files.

        Return deleted series files {series name: series file path}
        """
        deleted_series_files = {}
        for series in self.series:
            if series.path.exists():
                series.delete_file()
                deleted_series_files[series.title] = series.path
        self.series.clear()
        return deleted_series_files

    def check(self) -> bool:
        """Check regexps for the template.

        Create file from fields and after that parse it and compare parsed values
        with the initial fields
        """
        return self.check_regexes(
            {"Author name": {"value": lambda: self.name}},
            self._get_template().names_regexes[0].regex,
        )
