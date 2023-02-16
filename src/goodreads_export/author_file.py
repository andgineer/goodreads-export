"""Author's file."""  # pylint: disable=duplicate-code
import os
import urllib.parse
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, List, Optional

import jinja2

from goodreads_export.clean_file_name import clean_file_name
from goodreads_export.templates import AuthorTemplate, Templates


@dataclass
class AuthorFile:  # pylint: disable=too-many-instance-attributes
    """Author's file.

    On init extract fields from `content` - override other parameters.
    To re-parse the `content` call `parse()`.
    `render()` generate `content` from fields.
    """

    template: AuthorTemplate
    author: str
    folder: Path
    file_name: Optional[Path] = None
    content: Optional[str] = None
    names: Optional[list[str]] = field(init=False, default=None)

    _file_name: Optional[Path] = field(repr=False, init=False)
    _content: Optional[str] = field(repr=False, init=False)

    def __post_init__(self) -> None:
        """Extract fields from content."""
        self.jinja = jinja2.Environment()
        self.parse()  # we do not run parse on content assign during __init__()

    def parse(self) -> None:
        """Parse markdown file content."""
        if self._content is not None:
            self.names = None
            if regex := self.template.names_regexes.choose_regex(self._content):
                self.names = [
                    match[regex.name_group] for match in regex.compiled.finditer(self._content)
                ]
        if self.names is None:
            self.names = [self.author]

    def render(self) -> str:
        """Render markdown file content."""
        return self.template.body(self.jinja_context)

    @property
    def jinja_context(self) -> dict[str, Any]:
        """Jinja context."""
        return {
            "author": self.author,
            "urlencode": urllib.parse.urlencode,
            "clean_file_name": clean_file_name,
        }

    @property  # type: ignore
    def file_name(self) -> Path:
        """Markdown file name.

        Automatically generate file name from book's fields if not assigned.
        """
        if self._file_name is None:
            self._file_name = self.template.file_name(self.jinja_context)
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

    @property  # type: ignore  # same name as property
    def content(self) -> Optional[str]:
        """Markdown file content.

        Automatically generate content from book's fields if not assigned.
        """
        if self._content is None:
            self._content = self.render()
        return self._content

    @content.setter  # type: ignore  # same name as property
    def content(self, content: str) -> None:
        """Set content.

        Set None by default (if not in __init__() params)
        """
        if isinstance(content, property):
            self._content = None
            return
        self._content = content
        self.parse()

    def remove_non_primary_files(self) -> List[str]:
        """Remove files with non-primary author names.

        Return list of removed names.
        """
        assert self.names is not None  # to make mypy happy
        removed_names = []
        for name in self.names:
            if (
                name != self.author
                and (author_file_path := self.folder / f"{clean_file_name(name)}.md").exists()
            ):
                os.remove(author_file_path)
                removed_names += [name]
        return removed_names

    def write(self) -> None:
        """Write markdown file to path."""
        assert self.file_name is not None  # to please mypy
        assert self.content is not None  # to please mypy
        with (self.folder / self.file_name).open("w", encoding="utf8") as file:
            file.write(self.content)

    @classmethod
    def check(cls: type["AuthorFile"]) -> bool:
        """Check regex work for the template."""
        author_name = "Mark Twain"
        author_file = cls(Templates().author, author_name, Path())
        author_file.content = author_file.render()
        is_author_parsed = author_file.names == [author_name]
        if not is_author_parsed:
            print(f"Author name {author_name} is not parsed from content\n{author_file.content}")
            print(f"using the pattern\n{author_file.template.names_regexes[0].regex}")
        return is_author_parsed
