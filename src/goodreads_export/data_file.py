"""Object stored in the file."""
import os
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Optional

from goodreads_export.templates import FileTemplate

if TYPE_CHECKING:
    from goodreads_export.library import Library


class ParseError(Exception):
    """Error parsing content."""


class DataFile:
    """Object stored in the file."""

    library: "Library"
    folder: Optional[Path]

    _file_name: Optional[Path]
    _content: Optional[str]

    def __init__(
        self,
        *,
        library: "Library",
        folder: Optional[Path] = None,
        file_name: Optional[Path] = None,
        content: Optional[str] = None,
    ) -> None:
        """Set fields from args."""
        self.library = library
        self.folder = folder
        self._file_name = file_name
        self._content = content

    def _get_template(self) -> FileTemplate:
        """Template."""
        raise NotImplementedError()

    def _get_template_context(self) -> Dict[str, Any]:
        """Return template context."""
        raise NotImplementedError()

    @property
    def file_name(self) -> Path:
        """Markdown file name.

        Automatically generate file name from book's fields if not assigned.
        """
        if self._file_name is None:
            self._file_name = self._get_template().render_file_name(self._get_template_context())
        return self._file_name

    @file_name.setter
    def file_name(self, file_name: Path) -> None:
        """Set file_name."""
        self._file_name = file_name

    @property
    def file_link(self) -> str:
        """Return file link."""
        return self._get_template().render_file_link({"file_name": self.file_name})

    def render_body(self) -> str:
        """Return rendered body."""
        raise NotImplementedError()

    def parse(self) -> None:
        """Parse file content."""
        raise NotImplementedError()

    @property
    def content(self) -> str:
        """File content.

        Automatically generate content from object's fields if not assigned.
        """
        if self._content is None:
            self._content = self.render_body()
        return self._content

    @content.setter
    def content(self, content: str) -> None:
        """Set content and parse it."""
        self._content = content
        self.parse()

    def delete_file(self) -> None:
        """Delete the series file."""
        if self.path.exists():
            os.remove(self.path)

    @property
    def path(self) -> Path:
        """Return file path."""
        assert self.folder is not None
        return self.folder / self.file_name

    def write(self) -> None:
        """Write file to path."""
        self.path.write_text(self.content, encoding="utf8")
