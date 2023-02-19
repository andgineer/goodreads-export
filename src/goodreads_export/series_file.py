"""Series file."""
import urllib.parse
from dataclasses import dataclass, field
from functools import cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from goodreads_export.clean_file_name import clean_file_name
from goodreads_export.templates import templates


@dataclass
class SeriesFile:
    """Series' file."""

    author: Optional[str] = None
    title: Optional[str] = None
    file_name: Optional[Path] = None
    content: Optional[str] = None

    _file_name: Optional[Path] = field(init=False, repr=False)
    _content: Optional[str] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        """Extract fields from content."""
        self.parse()  # we do not run parse on content assign during __init__()

    def parse(self) -> None:
        """Parse file content."""
        if self._content is not None:
            self.title = None
            self.author = None
            if regex := templates.series.content_regexes.choose_regex(self._content):
                match = regex.compiled.search(self._content)
                assert match  # to make mypy happy
                self.title = match[regex.title_group]
                self.author = match[regex.author_group]

    @cache  # pylint: disable=method-cache-max-size-none
    def _template_context(self) -> Dict[str, Any]:
        """Return template context for series."""
        return {
            "series": self,
            "author": self.author,
            "urlencode": urllib.parse.urlencode,
            "clean_file_name": clean_file_name,
        }

    @classmethod
    def is_file_name(cls, file_name: Union[str, Path]) -> bool:
        """Return True if file name if indicate this is series description file."""
        return templates.series.file_name_regexes.choose_regex(str(file_name)) is not None

    @property  # type: ignore  # same name as property
    @cache  # pylint: disable=method-cache-max-size-none
    def file_name(self) -> Path:
        """Return file name for series."""
        if self._file_name is None:
            self._file_name = templates.series.render_file_name(self._template_context())
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

    @property
    @cache  # pylint: disable=method-cache-max-size-none
    def file_link(self) -> str:
        """Return file link for the series."""
        # todo send file name to context
        return templates.series.render_file_link(self._template_context())

    @classmethod
    @cache
    def file_suffix(cls) -> str:
        """File suffix."""
        file_name = SeriesFile(title="title", author="author").file_name
        assert file_name  # to make mypy happy
        return file_name.suffix

    def render_body(self) -> str:
        """Render series body."""
        return templates.series.render_body(self._template_context())

    @property  # type: ignore  # same name as property
    def content(self) -> Optional[str]:
        """File content.

        Automatically generate content from object's fields if not assigned.
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

    def __hash__(self) -> int:
        """Hash leveraging dataclasses __repr__."""
        return hash(self.__repr__())

    def __eq__(self, other: object) -> bool:
        """Compare two SeriesFile objects.

        Primary for @cache
        """
        if isinstance(other, SeriesFile):  # todo do not use class name explicitely
            return self.__hash__() == other.__hash__()
        raise NotImplementedError(f"Cannot compare SeriesFile with {type(other)}")


class SeriesList(List[SeriesFile]):
    """List of SeriesFile objects."""

    def by_title(self) -> Optional[SeriesFile]:
        """Find 1st series with the title."""
        return None
