"""Author's file."""  # pylint: disable=duplicate-code
import urllib.parse
from dataclasses import dataclass, field
from functools import cache
from pathlib import Path
from typing import Any, Dict, Optional

from goodreads_export.book_file import BookFile
from goodreads_export.clean_file_name import clean_file_name
from goodreads_export.data_file import DataFile
from goodreads_export.series_file import SeriesList
from goodreads_export.templates import AuthorTemplate, get_templates


@dataclass(kw_only=True, eq=False)
class AuthorFile(DataFile):  # pylint: disable=too-many-instance-attributes
    """Author's file.

    On init extract fields from `content` - override name(s).
    To re-parse the `content` call `parse()`.
    `render()` generate `content` from fields.
    """

    name: Optional[str] = field(default=None)  # primary author name
    names: list[str] = field(default_factory=list)
    series: SeriesList = field(default_factory=SeriesList, repr=False)
    books: list[BookFile] = field(default_factory=list, repr=False)

    def __post_init__(self) -> None:
        """Extract fields from content."""
        self.parse()  # we do not run parse on content assign during __init__()

    def _get_template(self) -> AuthorTemplate:  # type: ignore
        """Template."""
        return get_templates().author

    @cache  # pylint: disable=method-cache-max-size-none
    def _get_template_context(self) -> Dict[str, Any]:
        """Template context."""
        return {
            "author": self,
            "urlencode": urllib.parse.urlencode,
            "clean_file_name": clean_file_name,
        }

    def parse(self) -> None:
        """Parse file content.

        Set self.names to the names in the content and self.name to the first name.

        self.names is [] and no change in self.name if no names found in content.
        """
        if self._content is not None:
            self.names = []
            if regex := get_templates().author.names_regexes.choose_regex(self._content):
                self.names = [
                    match[regex.name_group] for match in regex.compiled.finditer(self._content)
                ]
                self.name = self.names[0]  # first name is primary

    def render_body(self) -> str:
        """Render file body."""
        return get_templates().author.render_body(self._get_template_context())  # type: ignore

    def write(self) -> None:
        """Write file to path."""
        assert self.file_name is not None  # to please mypy
        assert self.content is not None  # to please mypy
        assert self.folder is not None  # to please mypy
        with (self.folder / self.file_name).open("w", encoding="utf8") as file:
            file.write(self.content)

    def merge(self, other: "AuthorFile") -> None:
        """Merge other author with this one."""
        assert self.name is not None  # to please mypy
        for book in other.books:
            book.rename_author(self.name)
        for series in other.series:
            series.rename_author(self.name)
        self.books += other.books
        self.series += other.series
        other.delete_file()

    @classmethod
    def check(cls: type["AuthorFile"]) -> bool:
        """Check regex work for the template."""
        author_name = "Mark Twain"
        author_file = cls(name=author_name, folder=Path())
        author_file.content = author_file.render_body()
        is_author_parsed = author_file.names == [author_name]
        if not is_author_parsed:
            print(f"Author name {author_name} is not parsed from content\n{author_file.content}")
            print(f"using the pattern\n{get_templates().author.names_regexes[0].regex}")
        return is_author_parsed

    def __hash__(self) -> int:
        """Dataclass set it to None as it is not frozen."""
        return hash(self.__repr__())
