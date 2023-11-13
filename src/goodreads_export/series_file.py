"""Series object."""
import urllib.parse
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from goodreads_export.authored_file import AuthoredFile
from goodreads_export.data_file import ParseError
from goodreads_export.templates import SeriesTemplate


class SeriesFile(AuthoredFile):
    """Series' object."""

    title: str

    def __init__(self, *, title: Optional[str] = None, **kwargs: Any) -> None:
        """Set fields from args. Rewrite them from content if provided."""
        if title is not None:
            self.title = title
        super().__init__(**kwargs)

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
        assert self._content is not None, "Cannot parse None content"
        if regex := self._get_template().content_regexes.choose_regex(self._content):
            match = regex.compiled.search(self._content)
            assert match, (
                "impossible happened: after successful `search` in "
                "`choose_regex` got `None` for search with same params"
            )
            self.title = match[regex.title_group]
            self.author = self.library.author_factory(match[regex.author_group])
        else:
            raise ParseError(
                f"Cannot extract series information from file content:\n{self._content}"
            )

    def is_file_name(self, file_name: Union[str, Path]) -> bool:
        """Check `file_name` with series file name regex."""
        return self._get_template().file_name_regexes.choose_regex(str(file_name)) is not None

    def check(self) -> bool:
        """Check regexps for the template.

        Create file from fields and after that parse it and compare parsed values
        with the initial fields
        """
        fields_parsed = self.check_regexes(
            {
                "Series title": {"value": lambda: self.title},
                "Author name": {"value": lambda: self.author.name},
            },
            self._get_template().content_regexes[0].regex,
        )

        # force file name render and check the result
        self._file_name = None
        series_file_name = self.file_name
        is_file_name = self.is_file_name(series_file_name)
        if not is_file_name:
            print(f"Rendered with template `{self._get_template().file_name_template}`)")
            print(f"file name `{series_file_name}` is not recognized using the pattern:")
            print(f"{self._get_template().file_name_regexes[0].regex}")

        return fields_parsed and is_file_name


class SeriesList(List[SeriesFile]):
    """List of SeriesFile objects."""
