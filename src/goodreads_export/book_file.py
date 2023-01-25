"""Book's file."""
import re
import urllib.parse
from dataclasses import dataclass, field
from typing import List, Optional

from goodreads_export.clean_file_name import clean_file_name


@dataclass
class BookFile:  # pylint: disable=too-many-instance-attributes
    """Book's markdown file.

    On `content` assign (including init) extract fields from `content`.
    Data extracted from content will override init parameters.
    With `render()` can generate `content` from fields.
    """

    title: str
    file_name: Optional[str] = None
    _file_name: Optional[str] = field(repr=False, init=False)
    content: Optional[str] = None
    _content: Optional[str] = field(repr=False, init=False)
    author: Optional[str] = None
    _author: Optional[str] = field(repr=False, init=False)
    book_id: Optional[str] = None
    tags: Optional[List[str]] = None
    rating: Optional[int] = None
    isbn: Optional[int] = None
    isbn13: Optional[int] = None
    review: Optional[int] = None
    series: Optional[List[str]] = None

    _goodreads_link_pattern: re.Pattern[str] = field(
        repr=False,
        init=False,
        default=re.compile(
            r"\[\[([^]]+)\]\](: \[([^]]*)\]\(https://www\.goodreads\.com/book/show/(\d+)\))"
        ),
    )

    def __post_init__(self) -> None:
        """Extract fields from content."""
        self.parse()  # we do not run parse on content assign during __init__()
        if self._content is None:
            self.render()
        if self.tags is None:
            self.tags = []

    def parse(self) -> None:
        """Parse markdown file content."""
        if (
            self.content is not None
            and (book_match := self._goodreads_link_pattern.search(self.content)) is not None
        ):
            self.book_id = book_match[4]
            self.title = book_match[3]
            self._author = book_match[1]

    def render(self) -> None:
        """Render markdown file content."""
        assert self.book_id is not None
        assert self.title is not None
        assert self.author is not None
        assert self.tags is not None
        assert self.series is not None
        if "#book/book" not in self.tags:
            self.tags.append("#book/book")
        if self.rating is not None and self.rating > 0:
            rating_tag = f"#book/rating{self.rating}"
            if rating_tag not in self.tags:
                self.tags.append(rating_tag)
        book_url = f"https://www.goodreads.com/book/show/{self.book_id}"
        self._content = f"""
[[{clean_file_name(self.author)}]]: [{self.title}]({book_url})
ISBN{self.isbn} (ISBN13{self.isbn13})
{' '.join(['[[' + clean_file_name(series) + ']]' for series in self.series])}
{self.review}

[Search in Calibre](calibre://search/_?q={urllib.parse.quote(self.title)})

{" ".join(self.tags)}
"""

    @property  # type: ignore
    def content(self) -> str:
        """Markdown file content.

        Automatically render content if not assigned.
        """
        if self._content is None:
            self.render()
        assert self._content is not None
        return self._content

    @content.setter
    def content(self, content: str) -> None:
        """Set content and parse it extracting fields from it."""
        if isinstance(content, property):
            # do not run parse during __init__() - attributes values will be overwritten anyway
            self._content = None  # Set None by default (if not in __init__() params)
        else:
            self._content = content
            self.parse()

    @property  # type: ignore
    def author(self) -> Optional[str]:
        """Return author name."""
        return self._author

    @author.setter
    def author(self, author: str) -> None:
        """Set author name.

        Set None by default (if not in __init__() params)
        Replace the name in content.
        Do not use render to save user edits
        """
        if isinstance(author, property):
            self._author = None
            return
        # todo sub in content [[author]]$match[2]
        self._author = author

    @property  # type: ignore
    def file_name(self) -> str:
        """Markdown file name.

        Automatically generate file name from book's fields if not assigned.
        """
        if self._file_name is None:
            assert self.title is not None
            assert self.author is not None
            self._file_name = f"{clean_file_name(self.author)} - {clean_file_name(self.title)}.md"
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
