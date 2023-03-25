"""Library object with author."""
from abc import ABC
from typing import TYPE_CHECKING, Any, Optional

from goodreads_export.data_file import DataFile

if TYPE_CHECKING:
    from goodreads_export.library import AuthorFile


class AuthoredFile(DataFile, ABC):
    """Authored data file."""

    author: "AuthorFile"

    def __init__(self, *, author: Optional["AuthorFile"] = None, **kwargs: Any) -> None:
        """Set fields from args."""
        super().__init__(**kwargs)
        if author is not None:
            self.author = author

    def rename_author(self, new_author: str) -> None:
        """Rename author.

        We do not re-render the file fully to keep intact possible user changes in it.
        """
        self.delete_file()
        old_author_link = self.author.file_link
        self.author = self.library.get_author(new_author)
        self._file_name = None  # to force re-rendering
        self._content = self.content.replace(old_author_link, self.author.file_link)
        self.write()
