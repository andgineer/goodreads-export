"""Author's object."""
import urllib.parse
from typing import TYPE_CHECKING, Any, Dict, Optional

from goodreads_export.data_file import DataFile
from goodreads_export.series_file import SeriesList
from goodreads_export.templates import AuthorTemplate

if TYPE_CHECKING:
    from goodreads_export.book_file import BookFile


class AuthorFile(DataFile):
    """Author's object.

    On init extract `names` from `content` if defined.
    """

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
    ) -> None:  # pylint: disable=unused-argument
        """Set fields from args. Rewrite them from content if provided."""
        self.name = name
        self.names = names or []
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
        """Parse file content.

        Set self.names to the names in the content and self.name to the first name.

        self.names is [] and no change in self.name if no names found in content.
        """
        assert self._content is not None, "Cannot parse None content"
        self.names = []
        if regex := self._get_template().names_regexes.choose_regex(self._content):
            self.names = [
                match[regex.name_group] for match in regex.compiled.finditer(self._content)
            ]
            self.name = self.names[0]  # first name is primary

    def render_body(self) -> str:
        """Render file body."""
        return self._get_template().render_body(self._get_template_context())

    def merge(self, other: "AuthorFile") -> None:
        """Merge other author with this one."""
        for book in other.books:
            book.rename_author(self.name)
        for series in other.series:
            series.rename_author(self.name)
        self.books += other.books
        self.series += other.series
        other.delete_file()

    def check(self) -> bool:
        """Check regexps for the template.

        Create file from fields and after that parse it and compare parsed values with the initial fields
        """
        name = self.name
        self.content = self.render_body()
        is_author_parsed = self.names == [name]
        if not is_author_parsed:
            print(f"Author name {name} is not parsed from content\n{self.content}")
            print(f"using the pattern\n{self._get_template().names_regexes[0].regex}")
        return is_author_parsed
