"""Series file."""
import urllib.parse
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

from goodreads_export.data_file import DataFile
from goodreads_export.templates import SeriesTemplate, get_templates

if TYPE_CHECKING:
    from goodreads_export.library import AuthorFile


class SeriesFile(DataFile):  # pylint: disable=too-many-instance-attributes
    """Series' file."""

    author: Optional["AuthorFile"]
    title: Optional[str]

    def __init__(
        self, *, author: Optional["AuthorFile"] = None, title: Optional[str] = None, **kwargs: Any
    ) -> None:
        """Extract fields from content."""
        super().__init__(**kwargs)
        self.author = author
        self.title = title
        self.parse()

    def _get_template(self) -> SeriesTemplate:
        """Template."""
        return get_templates().series

    def _get_template_context(self) -> Dict[str, Any]:
        """Return template context for series."""
        return {
            "series": self,
            "author": self.author,
            "urlencode": urllib.parse.urlencode,
        }

    def parse(self) -> None:
        """Parse file content."""
        if self._content is not None:
            self.title = None
            self.author = None
            if regex := get_templates().series.content_regexes.choose_regex(self._content):
                match = regex.compiled.search(self._content)
                assert match  # to make mypy happy
                self.title = match[regex.title_group]
                self.author = self.library.get_author(match[regex.author_group])

    @classmethod
    def is_file_name(cls, file_name: Union[str, Path]) -> bool:
        """Return True if file name if indicate this is series description file."""
        return get_templates().series.file_name_regexes.choose_regex(str(file_name)) is not None

    def file_suffix(self) -> str:
        """File suffix."""
        file_name = self.file_name
        assert file_name  # to make mypy happy
        return file_name.suffix

    def render_body(self) -> str:
        """Render series body."""
        return get_templates().series.render_body(self._get_template_context())

    def write(self) -> None:
        """Write file to path."""
        assert self.content is not None  # to please mypy
        self.path.write_text(self.content, encoding="utf8")

    def check(self) -> bool:
        """Check regexps for the template.

        Create file from fields and after that parse it and compare parsed values with the initial fields
        """
        title = self.title
        assert self.author is not None  # to please mypy
        author_name = self.author.name
        self.content = self.render_body()
        is_title_parsed = self.title == title
        is_author_parsed = self.author.name == author_name
        if not is_title_parsed:
            print(f"Series title {title} is not parsed from content\n{self.content}")
            print(f"using the pattern\n{get_templates().series.content_regexes[0].regex}")
        if not is_author_parsed:
            print(f"Author name {author_name} is not parsed from content\n{self.content}")
            print(f"using the pattern\n{get_templates().series.content_regexes[0].regex}")
        series_file_name = self.file_name
        assert series_file_name is not None  # to please mypy
        is_file_name = self.is_file_name(series_file_name)
        if not is_file_name:
            print(f"Series file name {series_file_name} is not recognized")
            print(f"using the pattern\n{get_templates().series.file_name_regexes[0].regex}")
        return is_title_parsed and is_author_parsed and is_file_name

    def rename_author(self, new_author: str) -> None:
        """Rename author.

        We do not re-render the file fully to keep intact possible user changes in it.
        """
        self.delete_file()
        assert self.author is not None  # to please mypy
        assert self.content is not None  # to please mypy
        old_author_name = self.author.name
        self.author = self.library.get_author(new_author)
        self._file_name = None  # to force re-rendering
        self.content = self.content.replace(old_author_name, new_author)
        self.write()


class SeriesList(List[SeriesFile]):
    """List of SeriesFile objects."""

    def by_title(self) -> Optional[SeriesFile]:
        """Find 1st series with the title."""
        return None
