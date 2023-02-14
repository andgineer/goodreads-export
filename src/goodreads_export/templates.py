"""Templates for the Goodreads Exporter."""
import re
from dataclasses import dataclass, field
from importlib.resources import files
from typing import Dict, List, Optional, TypeVar

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib  # type: ignore


TEMPLATES_PACKAGE_DATA_FOLDER = "templates"


@dataclass
class RegEx:
    """Regular expression."""

    regex: str

    compiled: re.Pattern[str] = field(
        repr=False,
        init=False,
    )
    _compiled: Optional[re.Pattern[str]] = field(
        repr=False,
        init=False,
        default=None,
    )

    @property  # type: ignore
    def compiled(self) -> re.Pattern[str]:
        """Return compiled regex."""
        if self._compiled is None:
            self._compiled = re.compile(self.regex)
        return self._compiled

    @compiled.setter
    def compiled(self, value: re.Pattern[str]) -> None:
        """Fake setter.

        We autocompile it so this setter we need only to please dataclass.
        """


@dataclass
class AuthorNamesRegEx(RegEx):
    """Regular expressions for name links inside author's file."""

    # we need defaults because we have default in base class
    name_group: int = -1


@dataclass
class SeriesRegEx(RegEx):
    """Regular expressions for series links inside review file."""

    # we need defaults because we have default in base class
    series_group: int = -1


@dataclass
class GoodreadsLinkRegEx(RegEx):
    """Regular expressions for goodreads links inside review file."""

    # we need defaults because we have default in base class
    book_id_group: int = -1
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
    """Template for file with file name and body."""

    template: str

    body: str = field(init=False)
    file_name: str = field(init=False)

    def __post_init__(self) -> None:
        """Separate template to file name from first line and body from the rest.

        Second line ignored and use as visual separator.
        """
        object.__setattr__(self, "body", "\n".join(self.template.split("\n")[2:]))
        object.__setattr__(self, "file_name", self.template.split("\n", maxsplit=1)[0])


@dataclass(frozen=True)
class AuthorTemplate(FileTemplate):
    """Author template."""

    names_regexes: RegExList[AuthorNamesRegEx]


@dataclass(frozen=True)
class ReviewTemplate(FileTemplate):
    """Review template."""

    goodreads_link_regexes: RegExList[GoodreadsLinkRegEx]
    series_regexes: RegExList[SeriesRegEx]


@dataclass
class TemplateSet:
    """Template set to create all necessary files and parse existed ones."""

    name: str
    author: AuthorTemplate
    review: ReviewTemplate


class Templates:  # pylint: disable=too-few-public-methods
    """Templates injection.

    Loads embeded templates from package data.
    Loads template from BOOKS_FOLDER/templates - if exists it will be default.
    Otherwise default will be `default` from package data.
    """

    def __init__(self) -> None:
        """Load embeded templates from the package data."""
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
                        template=folder.joinpath("author.md").read_text(encoding="utf-8"),
                        names_regexes=RegExList(
                            [
                                AuthorNamesRegEx(**regex)
                                for regex in regex_config["regex"]["author"]["names"]
                            ]
                        ),
                    ),
                    review=ReviewTemplate(
                        template=folder.joinpath("review.md").read_text(encoding="utf-8"),
                        goodreads_link_regexes=RegExList(
                            [
                                GoodreadsLinkRegEx(**regex)
                                for regex in regex_config["regex"]["review"]["goodreads-link"]
                            ]
                        ),
                        series_regexes=RegExList(
                            [
                                SeriesRegEx(**regex)
                                for regex in regex_config["regex"]["review"]["series"]
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
    def review(self) -> ReviewTemplate:
        """Template for review."""
        return self.templates[self.selected].review
