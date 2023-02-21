"""Object stored in the file."""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from goodreads_export.templates import FileTemplate, get_templates


@dataclass
class DataFile:
    """Object stored in the file."""

    file_link: Optional[Path] = field(init=False, repr=False)

    _template: FileTemplate = field(default=get_templates().book, init=False, repr=False)

    # @cached_property  # type: ignore  # same name as property
    @property  # type: ignore  # same name as property
    def file_link(self) -> str:
        """Return file link."""
        return self._template.render_file_link({"file_name": self.file_name})  # type: ignore  # pylint: disable=no-member

    @file_link.setter
    def file_link(self, value: str) -> None:
        """To please dataclasses."""

    def __eq__(self, other: object) -> bool:
        """Compare two objects.

        Primary for @cache
        """
        if isinstance(other, self.__class__):
            return self.__hash__() == other.__hash__()
        raise NotImplementedError(f"Cannot compare {self.__class__} with {type(other)}")
