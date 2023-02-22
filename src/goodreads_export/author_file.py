"""Author's file."""  # pylint: disable=duplicate-code
import os
import urllib.parse
from dataclasses import dataclass, field
from functools import cache
from pathlib import Path
from typing import Any, Dict, List, Optional

from goodreads_export.clean_file_name import clean_file_name
from goodreads_export.series_file import SeriesList
from goodreads_export.templates import get_templates


@dataclass(eq=False)
class AuthorFile:  # pylint: disable=too-many-instance-attributes
    """Author's file.

    On init extract fields from `content` - override other parameters.
    To re-parse the `content` call `parse()`.
    `render()` generate `content` from fields.
    """

    folder: Path
    name: Optional[str] = field(default=None)  # primary author name
    file_name: Optional[Path] = field(default=None, repr=False)
    content: Optional[str] = field(default=None, repr=False)
    names: Optional[list[str]] = field(init=False, default=None)
    series: SeriesList = field(default_factory=SeriesList, repr=False)

    _file_name: Optional[Path] = field(init=False)
    _content: Optional[str] = field(init=False)

    def __post_init__(self) -> None:
        """Extract fields from content."""
        self._template = get_templates().author
        self.parse()  # we do not run parse on content assign during __init__()

    @property
    @cache  # pylint: disable=method-cache-max-size-none
    def _template_context(self) -> Dict[str, Any]:
        """Template context."""
        return {
            "author": self,
            "urlencode": urllib.parse.urlencode,
            "clean_file_name": clean_file_name,
        }

    def parse(self) -> None:
        """Parse file content."""
        if self._content is not None:
            assert self.file_name  # to make mypy happy
            self.name = self.file_name.stem
            self.names = None
            if regex := get_templates().author.names_regexes.choose_regex(self._content):
                self.names = [
                    match[regex.name_group] for match in regex.compiled.finditer(self._content)
                ]
        if self.names is None and self.name is not None:
            self.names = [self.name]

    def render_body(self) -> str:
        """Render file body."""
        return get_templates().author.render_body(self._template_context)  # type: ignore

    @property  # type: ignore
    def file_name(self) -> Path:
        """Markdown file name.

        Automatically generate file name from book's fields if not assigned.
        """
        if self._file_name is None:
            self._file_name = get_templates().author.render_file_name(self._template_context)  # type: ignore
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

    def remove_non_primary_files(self) -> List[str]:
        """Remove files with non-primary author names.

        Return list of removed names.
        """
        assert self.names is not None  # to make mypy happy
        removed_names = []
        for name in self.names:
            if (
                name != self.name
                and (author_file_path := self.folder / f"{clean_file_name(name)}.md").exists()
            ):
                os.remove(author_file_path)
                removed_names += [name]
        return removed_names

    def write(self) -> None:
        """Write file to path."""
        assert self.file_name is not None  # to please mypy
        assert self.content is not None  # to please mypy
        with (self.folder / self.file_name).open("w", encoding="utf8") as file:
            file.write(self.content)

    @classmethod
    def check(cls: type["AuthorFile"]) -> bool:
        """Check regex work for the template."""
        author_name = "Mark Twain"
        author_file = cls(name=author_name, folder=Path())
        author_file.content = author_file.render_body()
        is_author_parsed = author_file.names == [author_name]
        if not is_author_parsed:
            print(f"Author name {author_name} is not parsed from content\n{author_file.content}")
            print(f"using the pattern\n{get_templates().author.names_regexes[0].regex}")
        return is_author_parsed

    def __hash__(self) -> int:
        """Dataclass set it to None as it is not frozen."""
        return hash(self.__repr__())
