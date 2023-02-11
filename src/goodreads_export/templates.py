"""Templates for the Goodreads Exporter."""
import re
from dataclasses import dataclass, field
from importlib.resources import files
from typing import Dict, List, Optional

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib  # type: ignore


TEMPLATES_PACKAGE_DATA_FOLDER = "templates"


@dataclass
class AuthorNamesRegEx:
    """Regular expressions for author's file."""

    regex: str
    name_group: int

    compiled: Optional[re.Pattern[str]] = field(
        repr=False,
        init=False,
        default=None,
    )


@dataclass
class AuthorTemplate:
    """Author template."""

    author_template: str
    names_regexes: List[AuthorNamesRegEx]


@dataclass
class Template:
    """Template."""

    name: str
    author: AuthorTemplate


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

    def load_embeded(self) -> Dict[str, Template]:
        """Load embeded template.

        From the package data folder `templates` recursively.
        """
        result = {}
        templates_resource = files(__package__).joinpath(TEMPLATES_PACKAGE_DATA_FOLDER)
        for folder in templates_resource.iterdir():
            if folder.is_dir():
                regex_config = tomllib.loads(folder.joinpath("regex.toml").read_text())
                result[folder.name] = Template(
                    name=folder.name,
                    author=AuthorTemplate(
                        author_template=folder.joinpath("author.md").read_text(),
                        names_regexes=[
                            AuthorNamesRegEx(**regex)
                            for regex in regex_config["regex"]["author"]["names"]
                        ],
                    ),
                )
        return result

    @property
    def author(self) -> AuthorTemplate:
        """Template for author."""
        return self.templates[self.selected].author
