"""Author's file."""  # pylint: disable=duplicate-code
import os
import re
import urllib.parse
from dataclasses import dataclass, field
from importlib.resources import files
from pathlib import Path
from typing import List, Optional

from goodreads_export.clean_file_name import clean_file_name


@dataclass
class AuthorFile:  # pylint: disable=too-many-instance-attributes
    """Author's file.

    On init extract fields from `content` - override other parameters.
    To re-parse the `content` call `parse()`.
    `render()` generate `content` from fields.
    """

    author: str
    folder: Path
    file_name: Optional[str] = None
    _file_name: Optional[str] = field(repr=False, init=False)
    content: Optional[str] = None

    _name_link_pattern: re.Pattern[str] = field(
        repr=False,
        init=False,
        default=re.compile(
            r"\[([^]]*)\]\(https://www\.goodreads\.com/search\?utf8=%E2%9C%93&q=[^&]*"
            r"&search_type=books&search%5Bfield%5D=author\)"
        ),
    )
    names: Optional[list[str]] = field(init=False, default=None)

    def __post_init__(self) -> None:
        """Extract fields from content."""
        self.parse()  # we do not run parse on content assign during __init__()
        if self.content is None:
            self.render()
        # todo inject Template
        self.template = (
            files(__package__)
            .joinpath("themes")
            .joinpath("default")
            .joinpath("author.md")
            .read_text()
        )

    def parse(self) -> None:
        """Parse markdown file content."""
        if self.content is not None:
            self.names = [match[1] for match in self._name_link_pattern.finditer(self.content)]
        elif self.names is None:
            self.names = [self.author]

    def render(self) -> None:
        """Render markdown file content."""
        search_params = urllib.parse.urlencode(
            {
                "utf8": "✓",
                "q": self.author,
                "search_type": "books",
                "search[field]": "author",
            }
        )
        self.content = f"""[{self.author}](https://www.goodreads.com/search?{search_params})

#book/author
"""

    @property  # type: ignore
    def file_name(self) -> str:
        """Markdown file name.

        Automatically generate file name from book's fields if not assigned.
        """
        # todo read template from file
        if self._file_name is None:
            self._file_name = f"{clean_file_name(self.author)}.md"
        return self._file_name

    @file_name.setter
    def file_name(self, file_name: str) -> None:
        """Set file_name.

        Set None by default (if not in __init__() params)
        """
        if isinstance(file_name, property):
            self._file_name = None
            return
        self._file_name = file_name

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
        book_file = cls(author_name, Path())
        book_file.names = []
        book_file.parse()
        is_author_parsed = book_file.names == [author_name]
        if not is_author_parsed:
            print(f"Author name {author_name} is not parsed from content\n{book_file.content}")
            print(f"using the pattern\n{book_file._name_link_pattern.pattern}")
        return is_author_parsed
