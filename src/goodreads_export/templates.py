"""Templates for the Goodreads Exporter."""
import dataclasses
from importlib.resources import files
from typing import Any, Dict

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib  # type: ignore


TEMPLATES_PACKAGE_DATA_FOLDER = "templates"


@dataclasses.dataclass
class Template:
    """Template."""

    name: str
    author_template: str
    regex: Dict[str, Any]


class Templates:  # pylint: disable=too-few-public-methods
    """Templates injection.

    Loads embeded templates from package data.
    Loads template from BOOKS_FOLDER/templates - if exists it will be default.
    Otherwise default will be `default` from package data.
    """

    def __init__(self) -> None:
        """Load embeded templates from the package data."""
        self.templates = self.load_embeded()

    def load_embeded(self) -> Dict[str, Template]:
        """Load embeded template.

        From the package data folder `templates` recursively.
        """
        result = {}
        templates_resource = files(__package__).joinpath(TEMPLATES_PACKAGE_DATA_FOLDER)
        for folder in templates_resource.iterdir():
            if folder.is_dir():
                result[folder.name] = Template(
                    name=folder.name,
                    author_template=folder.joinpath("author.md").read_text(),
                    regex=tomllib.loads(folder.joinpath("regex.toml").read_text()),
                )
        return result
