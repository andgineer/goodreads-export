"""Templates for the Goodreads Exporter."""
import re
from dataclasses import dataclass, field
from importlib.resources import files
from pathlib import Path
from typing import Any, Dict, List, Optional, TypeVar

import jinja2
from jinja2 import DebugUndefined

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib  # type: ignore


TEMPLATES_PACKAGE_DATA_FOLDER = "templates"
BOOK_TEMPLATE_FILE_NAME = "book.jinja"
AUTHOR_TEMPLATE_FILE_NAME = "author.jinja"
SERIES_TEMPLATE_FILE_NAME = "series.jinja"


@dataclass(frozen=True)
class RegEx:
    """Regular expression."""

    regex: str

    compiled: re.Pattern[str] = field(init=False)

    def __post_init__(self) -> None:
        """Compile regex."""
        object.__setattr__(self, "compiled", re.compile(self.regex))


@dataclass(frozen=True)
class AuthorNamesRegEx(RegEx):
    """Regular expressions for name links inside author's file."""

    # we need defaults because we have default in base class
    name_group: int = -1


@dataclass(frozen=True)
class BookSeriesRegEx(RegEx):
    """Regular expressions for series links inside review file."""

    # we need defaults because we have default in base class
    series_group: int = -1


@dataclass(frozen=True)
class BookGoodreadsLinkRegEx(RegEx):
    """Regular expressions for goodreads links inside review file."""

    # we need defaults because we have default in base class
    book_id_group: int = -1
    title_group: int = -1
    author_group: int = -1


@dataclass(frozen=True)
class SeriesFileNameRegEx(RegEx):
    """Regular expressions for series file name.

    We only match it so no need in any groups.
    """


@dataclass(frozen=True)
class SeriesContentRegEx(RegEx):
    """Regular expressions for series file."""

    # we need defaults because we have default in base class
    title_group: int = -1
    author_group: int = -1


RegExSubClass = TypeVar("RegExSubClass", bound=RegEx)


class RegExList(List[RegExSubClass]):
    """List of regular expressions."""

    def choose_regex(self, content: str) -> Optional[RegExSubClass]:
        """Choose regex that matches the content."""
        if content is not None:
            for regex in self:
                assert regex.compiled is not None  # to please mypy
                if regex.compiled.search(content) is not None:
                    assert issubclass(regex.__class__, RegEx)
                    return regex
        return None


@dataclass(frozen=True)
class FileTemplate:
    """Template for file with file name, optional link and body.

    1st line - template for the file name.

    If 2nd line is not empty - it is optional link.
    Otherwise link is file name without extension and folders part.

    After file name and optional link templates should be empty line and then file body template.
    """

    template: str

    body_template: str = field(init=False)
    file_name_template: str = field(init=False)
    file_link_template: str = field(init=False)

    env: "Templates" = field(repr=False)

    def __post_init__(self) -> None:
        """Split template to file name, optional link and body."""
        object.__setattr__(self, "file_name_template", self.template.split("\n", maxsplit=1)[0])
        if self.template.split("\n", maxsplit=2)[1] != "":
            file_link_template = self.template.split("\n", maxsplit=2)[1]
            body_template = "\n".join(self.template.split("\n")[3:])
        else:
            file_link_template = None
            body_template = "\n".join(self.template.split("\n")[2:])
        object.__setattr__(self, "file_link_template", file_link_template)
        object.__setattr__(self, "body_template", body_template)

    def render_file_name(self, context: Dict[str, Any]) -> Path:
        """Render file name with context."""
        return Path(self.env.jinja.from_string(self.file_name_template).render(context))

    def render_file_link(self, context: Dict[str, Any]) -> str:
        """Render link with context.

        If link template is not defined - return file name without extension and folders part.
        """
        if self.file_link_template is None:
            return Path(context["file_name"]).stem
        return self.env.jinja.from_string(self.file_link_template).render(context)

    def render_body(self, context: Dict[str, Any]) -> str:
        """Render file body with context."""
        return self.env.jinja.from_string(self.body_template).render(context)


@dataclass(frozen=True)
class AuthorTemplate(FileTemplate):
    """Author template."""

    names_regexes: RegExList[AuthorNamesRegEx]


@dataclass(frozen=True)
class SeriesTemplate(FileTemplate):
    """Series template."""

    content_regexes: RegExList[SeriesContentRegEx]
    file_name_regexes: RegExList[SeriesFileNameRegEx]


@dataclass(frozen=True)
class BookTemplate(FileTemplate):
    """Book template."""

    goodreads_link_regexes: RegExList[BookGoodreadsLinkRegEx]
    series_regexes: RegExList[BookSeriesRegEx]


@dataclass
class TemplateSet:
    """Template set to create all necessary files and parse existed ones."""

    name: str
    author: AuthorTemplate
    book: BookTemplate
    series: SeriesTemplate


class Templates:  # pylint: disable=too-few-public-methods
    """Templates injection.

    Loads embeded templates from package data.
    Loads template from BOOKS_FOLDER/templates - if exists it will be default.
    Otherwise default will be `default` from package data.
    """

    jinja = jinja2.Environment()

    def __init__(self, debug: bool = False) -> None:
        """Load embeded templates from the package data."""
        if debug:
            self.jinja = jinja2.Environment(undefined=DebugUndefined)
        self.templates = self.load_embeded()
        self.selected = "default"

    def load_embeded(self) -> Dict[str, TemplateSet]:
        """Load embeded template.

        From the package data folder `templates` recursively.
        """
        result = {}
        templates_resource = files(__package__).joinpath(TEMPLATES_PACKAGE_DATA_FOLDER)
        for folder in templates_resource.iterdir():
            if folder.is_dir():
                regex_config = tomllib.loads(
                    folder.joinpath("regex.toml").read_text(encoding="utf-8")
                )
                result[folder.name] = TemplateSet(
                    name=folder.name,
                    author=AuthorTemplate(
                        env=self,
                        template=folder.joinpath(AUTHOR_TEMPLATE_FILE_NAME).read_text(
                            encoding="utf-8"
                        ),
                        names_regexes=RegExList(
                            [
                                AuthorNamesRegEx(**regex)
                                for regex in regex_config["regex"]["author"]["names"]
                            ]
                        ),
                    ),
                    book=BookTemplate(
                        env=self,
                        template=folder.joinpath(BOOK_TEMPLATE_FILE_NAME).read_text(
                            encoding="utf-8"
                        ),
                        goodreads_link_regexes=RegExList(
                            [
                                BookGoodreadsLinkRegEx(**regex)
                                for regex in regex_config["regex"]["book"]["goodreads-link"]
                            ]
                        ),
                        series_regexes=RegExList(
                            [
                                BookSeriesRegEx(**regex)
                                for regex in regex_config["regex"]["book"]["series"]
                            ]
                        ),
                    ),
                    series=SeriesTemplate(
                        env=self,
                        template=folder.joinpath(SERIES_TEMPLATE_FILE_NAME).read_text(
                            encoding="utf-8"
                        ),
                        content_regexes=RegExList(
                            [
                                SeriesContentRegEx(**regex)
                                for regex in regex_config["regex"]["series"]["content"]
                            ]
                        ),
                        file_name_regexes=RegExList(
                            [
                                SeriesFileNameRegEx(**regex)
                                for regex in regex_config["regex"]["series"]["file-name"]
                            ]
                        ),
                    ),
                )
        return result

    @property
    def author(self) -> AuthorTemplate:
        """Template for author."""
        return self.templates[self.selected].author

    @property
    def book(self) -> BookTemplate:
        """Template for review."""
        return self.templates[self.selected].book

    @property
    def series(self) -> SeriesTemplate:
        """Template for review."""
        return self.templates[self.selected].series


_templates = Templates()


def get_templates() -> Templates:
    """Get templates singleton."""
    return _templates
