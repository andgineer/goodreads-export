"""Series file."""
import urllib.parse
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from goodreads_export.clean_file_name import clean_file_name
from goodreads_export.data_file import DataFile
from goodreads_export.templates import SeriesTemplate, get_templates


class SeriesFile(DataFile):  # pylint: disable=too-many-instance-attributes
    """Series' file."""

    author: Optional[str]
    title: Optional[str]

    def __init__(
        self, *, author: Optional[str] = None, title: Optional[str] = None, **kwargs: Any
    ) -> None:
        """Extract fields from content."""
        super().__init__(**kwargs)
        self.author = author
        self.title = title
        self.parse()

    def _get_template(self) -> SeriesTemplate:
        """Template."""
        return get_templates().series

    def _get_template_context(self) -> Dict[str, Any]:
        """Return template context for series."""
        return {
            "series": self,
            "author": self.author,
            "urlencode": urllib.parse.urlencode,
            "clean_file_name": clean_file_name,
        }

    def parse(self) -> None:
        """Parse file content."""
        if self._content is not None:
            self.title = None
            self.author = None
            if regex := get_templates().series.content_regexes.choose_regex(self._content):
                match = regex.compiled.search(self._content)
                assert match  # to make mypy happy
                self.title = match[regex.title_group]
                self.author = match[regex.author_group]

    @classmethod
    def is_file_name(cls, file_name: Union[str, Path]) -> bool:
        """Return True if file name if indicate this is series description file."""
        return get_templates().series.file_name_regexes.choose_regex(str(file_name)) is not None

    @classmethod
    def file_suffix(cls) -> str:
        """File suffix."""
        file_name = SeriesFile(title="title", author="author").file_name
        assert file_name  # to make mypy happy
        return file_name.suffix

    def render_body(self) -> str:
        """Render series body."""
        return get_templates().series.render_body(self._get_template_context())

    def write(self) -> None:
        """Write file to path."""
        assert self.content is not None  # to please mypy
        self.path.write_text(self.content, encoding="utf8")

    @classmethod
    def check(cls: type["SeriesFile"]) -> bool:
        """Check regex work for the template."""
        author_name = "Mark Twain"
        title = "title"
        series_file = cls(title=title, author=author_name)
        series_file.content = series_file.render_body()
        is_title_parsed = series_file.title == title
        is_author_parsed = series_file.author == author_name
        if not is_title_parsed:
            print(f"Series title {title} is not parsed from content\n{series_file.content}")
            print(f"using the pattern\n{get_templates().series.content_regexes[0].regex}")
        if not is_author_parsed:
            print(f"Author name {author_name} is not parsed from content\n{series_file.content}")
            print(f"using the pattern\n{get_templates().series.content_regexes[0].regex}")
        series_file_name = series_file.file_name
        assert series_file_name is not None  # to please mypy
        is_file_name = cls.is_file_name(series_file_name)
        if not is_file_name:
            print(f"Series file name {series_file_name} is not recognized")
            print(f"using the pattern\n{get_templates().series.file_name_regexes[0].regex}")
        return is_title_parsed and is_author_parsed and is_file_name

    def rename_author(self, new_author: str) -> None:
        """Rename author.

        We do not re-render the file fully to keep intact possible user changes in it.
        """
        self.delete_file()
        assert self.author is not None  # to please mypy
        assert self.content is not None  # to please mypy
        old_author_name = self.author
        self.author = new_author
        self._file_name = None  # to force re-rendering
        self.content = self.content.replace(old_author_name, new_author)
        self.write()


class SeriesList(List[SeriesFile]):
    """List of SeriesFile objects."""

    def by_title(self) -> Optional[SeriesFile]:
        """Find 1st series with the title."""
        return None
