"""Series object."""
import urllib.parse
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from goodreads_export.authored_file import AuthoredFile
from goodreads_export.data_file import ParseError
from goodreads_export.templates import SeriesTemplate


class SeriesFile(AuthoredFile):
    """Series' object."""

    title: Optional[str]

    def __init__(self, *, title: Optional[str] = None, **kwargs: Any) -> None:
        """Extract fields from content."""
        super().__init__(**kwargs)
        self.title = title
        self.parse()

    def _get_template(self) -> SeriesTemplate:
        """Template."""
        return self.library.templates.series

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
            if regex := self._get_template().content_regexes.choose_regex(self._content):
                match = regex.compiled.search(self._content)
                assert match  # to make mypy happy
                self.title = match[regex.title_group]
                self.author = self.library.get_author(match[regex.author_group])
            else:
                raise ParseError(
                    f"Cannot extract series information from file content:\n{self._content}"
                )

    def is_file_name(self, file_name: Union[str, Path]) -> bool:
        """Return True if file name if indicate this is series description file."""
        return self._get_template().file_name_regexes.choose_regex(str(file_name)) is not None

    def render_body(self) -> str:
        """Render series body."""
        return self._get_template().render_body(self._get_template_context())

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
            print(f"using the pattern\n{self._get_template().content_regexes[0].regex}")
        if not is_author_parsed:
            print(f"Author name {author_name} is not parsed from content\n{self.content}")
            print(f"using the pattern\n{self._get_template().content_regexes[0].regex}")
        series_file_name = self.file_name
        assert series_file_name is not None  # to please mypy
        is_file_name = self.is_file_name(series_file_name)
        if not is_file_name:
            print(f"Series file name {series_file_name} is not recognized")
            print(f"using the pattern\n{self._get_template().file_name_regexes[0].regex}")
        return is_title_parsed and is_author_parsed and is_file_name


class SeriesList(List[SeriesFile]):
    """List of SeriesFile objects."""

    def by_title(self) -> Optional[SeriesFile]:
        """Find 1st series with the title."""
        return None
