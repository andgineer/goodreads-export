"""Object stored in the file."""
import os
from dataclasses import dataclass, field
from functools import cache
from pathlib import Path
from typing import Any, Dict, Optional

from goodreads_export.templates import FileTemplate


@dataclass(kw_only=True)
class DataFile:
    """Object stored in the file."""

    folder: Path
    file_name: Path = field(default=Path(), repr=False)
    file_link: Optional[Path] = field(init=False, repr=False)
    content: Optional[str] = field(default=None, repr=False)

    _file_name: Optional[Path] = field(default=None, init=False)
    _content: Optional[str] = field(init=False)

    def _get_template(self) -> FileTemplate:
        """Template."""
        raise NotImplementedError()

    @cache  # pylint: disable=method-cache-max-size-none
    def _get_template_context(self) -> Dict[str, Any]:
        """Return template context."""
        raise NotImplementedError()

    @property  # type: ignore
    def file_name(self) -> Path:
        """Markdown file name.

        Automatically generate file name from book's fields if not assigned.
        """
        if self._file_name is None:
            self._file_name = self._get_template().render_file_name(self._get_template_context())
        return self._file_name

    @file_name.setter
    def file_name(self, file_name: Path) -> None:
        """Set file_name.

        Set None by default (if not in __init__() params) or from default Path()
        So consequent calls to file_name will render it with template.
        """
        if isinstance(file_name, property) or file_name == Path():
            self._file_name = None
            return
        self._file_name = file_name

    # @cached_property  # type: ignore  # same name as property
    @property  # type: ignore  # same name as property
    def file_link(self) -> str:
        """Return file link."""
        return self._get_template().render_file_link({"file_name": self.file_name})

    @file_link.setter
    def file_link(self, value: str) -> None:
        """To please dataclasses."""

    def render_body(self) -> Optional[str]:
        """Return rendered body."""
        raise NotImplementedError()

    def parse(self) -> None:
        """Parse file content."""
        raise NotImplementedError()

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

    def delete_file(self) -> None:
        """Delete the series file."""
        if (self.folder / self.file_name).exists():
            os.remove(self.folder / self.file_name)

    def __eq__(self, other: object) -> bool:
        """Compare two objects.

        Primary for @cache
        """
        if isinstance(other, self.__class__):
            return self.__hash__() == other.__hash__()
        raise NotImplementedError(f"Cannot compare {self.__class__} with {type(other)}")
