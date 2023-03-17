"""Create md-files from https://www.goodreads.com/ CSV export."""
import os
import sys
from pathlib import Path
from typing import Optional

import click

from goodreads_export.goodreads_book import GoodreadsBooks
from goodreads_export.library import Library
from goodreads_export.log import Log
from goodreads_export.templates import DEFAULT_BUILTIN_TEMPLATE, TemplateSet, TemplatesLoader
from goodreads_export.version import VERSION

GOODREAD_EXPORT_FILE_NAME = "goodreads_library_export.csv"
DEFAULT_TEMPLATES_FOLDER = "./templates"

VERBOSE_OPTION = click.option(
    "--verbose",
    "-v",
    "verbose",
    is_flag=True,
    default=False,
    help="""Increase verbosity.""",
    nargs=1,
)

TEMPLATES_FOLDER_OPTION = click.option(
    "--templates-folder",
    "-t",
    "templates_folder",
    default=None,
    type=click.Path(path_type=Path),
    help=f"""Folder with templates.
By default look for `{DEFAULT_TEMPLATES_FOLDER}` in folder with books,
use embedded templates `{DEFAULT_BUILTIN_TEMPLATE}` if not found""",
    nargs=1,
)

BUILTIN_TEMPLATES_NAME_OPTION = click.option(
    "--builtin-name",
    "-b",
    "builtin_name",
    default=None,
    help="""Name of the built-in template.""",
    nargs=1,
)


BOOKS_FOLDER_OPTION = click.argument(
    "books_folder",
    default=".",
    type=click.Path(exists=True, path_type=Path),
    nargs=1,
)


def merge_authors(log: Log, books_folder: Path, templates: TemplateSet) -> Library:
    """Merge authors."""
    library = Library(folder=books_folder, log=log, templates=templates)
    log.start(f"Reading existing files from {library}")
    print(
        f" loaded {len(library.books)} books, {len(library.authors)} authors, "
        f"skipped {library.stat.skipped_unknown_files} unknown files"
        f" and {library.stat.series_added} series files.",
    )
    library.merge_author_names()
    return library


def load_templates(
    log: Log,
    books_folder: Path,
    templates_folder: Optional[Path],
    builtin_templates_name: Optional[str],
) -> TemplateSet:
    """Load templates.

    If templates_folder is not None, load from this folder.
    Else load embedded templated with specified or default name.
    If the temples_folder is None and builtin_name is not None,
    but default templates folder exists, notify that we ignore it.
    """
    if builtin_templates_name is not None and templates_folder is not None:
        log.error("You can't use both --templates-name and --templates-folder")
        sys.exit(1)
    try:
        if templates_folder is None:
            if (books_folder / DEFAULT_TEMPLATES_FOLDER).is_dir():
                if builtin_templates_name is None:
                    return TemplatesLoader().load_folder(books_folder / DEFAULT_TEMPLATES_FOLDER)
                log.info(
                    f"Using embedded templates `{builtin_templates_name}, "
                    f"ignore templates in `{DEFAULT_TEMPLATES_FOLDER}`."
                )
                return TemplatesLoader().load_builtin(builtin_templates_name)
            if builtin_templates_name is None:
                return TemplatesLoader().load_builtin()
        elif not templates_folder.is_absolute():
            templates_folder = books_folder / templates_folder
        if builtin_templates_name is not None:
            return TemplatesLoader().load_builtin(builtin_templates_name)
        assert templates_folder is not None  # for mypy
        return TemplatesLoader().load_folder(templates_folder)
    except Exception as exc:  # pylint: disable=broad-except
        log.error(f"Error loading templates: {exc}")
        sys.exit(1)


@click.group(invoke_without_command=True)
@click.pass_context
@click.option(
    "--version",
    "version",
    is_flag=True,
    default=False,
    help="Show version.",
    nargs=1,
)
def main(ctx: click.Context, version: bool) -> None:
    """Create md-files from https://www.goodreads.com/ CSV export.

    For example, you can create nice structure in Obsidian.

    How to create goodreads export see in https://www.goodreads.com/review/import
    In 2022 they declare it to be removed by August,
    but at least at the end of 2022 it still works.

    Documentation https://andgineer.github.io/goodreads-export/

    To see help on the commands use `goodreads-export COMMAND --help`.
    For example: `goodreads-export import --help`.
    """
    try:
        if version:
            print(f"{VERSION}")
            sys.exit(0)
        if not ctx.invoked_subcommand:
            click.echo("Error: Missing command.")
            click.echo(main.get_help(ctx))
            sys.exit(1)
    except Exception as exc:  # pylint: disable=broad-except
        print(f"\n{exc}")
        sys.exit(1)


@main.command(name="import")
@BOOKS_FOLDER_OPTION
@VERBOSE_OPTION
@TEMPLATES_FOLDER_OPTION
@BUILTIN_TEMPLATES_NAME_OPTION
@click.option(
    "--in",
    "-i",
    "csv_file",
    default=GOODREAD_EXPORT_FILE_NAME,
    help="""Goodreads export file. By default `goodreads_library_export.csv`.
if you specify just folder it will look for file with this name in that folder.""",
    nargs=1,
)
def import_(
    verbose: bool,
    csv_file: str,
    books_folder: Path,
    templates_folder: Optional[Path],
    builtin_name: Optional[str],
) -> None:
    """Convert goodreads export CSV file to markdown files.

    BOOKS_FOLDER
    Folder where we put result. By default, current folder.
    If the folder already exists also merge authors if found author files with many names.

    Documentation https://andgineer.github.io/goodreads-export/
    """
    try:
        log = Log(verbose)

        if os.path.isdir(
            csv_file
        ):  # if folder as csv_file try to find goodreads file in that folder
            csv_file = os.path.join(csv_file, GOODREAD_EXPORT_FILE_NAME)
        if not os.path.isfile(csv_file):
            print(f"Goodreads export file '{csv_file}' not found.")
            sys.exit(1)
        log.start(f"Loading reviews from {csv_file}")
        books = GoodreadsBooks(csv_file)
        print(f" loaded {len(books)} reviews.")
        library = merge_authors(
            log=log,
            books_folder=books_folder,
            templates=load_templates(log, books_folder, templates_folder, builtin_name),
        )
        library.dump(books)
        print(
            f"\nAdded {library.stat.books_added} review files, "
            f"{library.stat.authors_added} author files.",
            f"Renamed {library.stat.authors_renamed} authors.",
        )

    except Exception as exc:  # pylint: disable=broad-except
        print(f"\n{exc}")
        sys.exit(1)


@main.command()
@BOOKS_FOLDER_OPTION
@VERBOSE_OPTION
@TEMPLATES_FOLDER_OPTION
@BUILTIN_TEMPLATES_NAME_OPTION
def check(
    verbose: bool,
    books_folder: Path,
    templates_folder: Optional[Path],
    builtin_name: Optional[str],
) -> None:
    """Check templates consistency with extraction regexes.

    Loads templates and regexes from books_folder/templates.
    To create initial files from embedded default use command `goodreads-export init`.

    BOOKS_FOLDER
    Folder with books file to check.
    Loads templetes if they are existed in the folder and `-templates-name` is not specified.
    """
    try:
        log = Log(verbose)
        library = Library(  # to run template checks we do not want changes in fs, so no `folder` argument
            log=log, templates=load_templates(log, books_folder, templates_folder, builtin_name)
        )
        library.check_templates()
        log.info("Templates are consistent with extraction regexes.")
    except Exception as exc:  # pylint: disable=broad-except
        print(f"\n{exc}")
        sys.exit(1)


@main.command()
@BOOKS_FOLDER_OPTION
@VERBOSE_OPTION
@TEMPLATES_FOLDER_OPTION
@BUILTIN_TEMPLATES_NAME_OPTION
def merge(
    verbose: bool,
    books_folder: Path,
    templates_folder: Optional[Path],
    builtin_name: Optional[str],
) -> None:
    """Merge authors only.

    Use it if you need only re-link to primary author names
    without importing goodreads file.

    BOOKS_FOLDER
    Folder to merge authors. By default, current folder.

    See https://andgineer.github.io/goodreads-export/ for details.
    """
    try:
        log = Log(verbose)
        library = merge_authors(
            log=log,
            books_folder=books_folder,
            templates=load_templates(log, books_folder, templates_folder, builtin_name),
        )
        print(
            f"Renamed {library.stat.authors_renamed} authors.",
        )
    except Exception as exc:  # pylint: disable=broad-except
        print(f"\n{exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()  # pylint: disable=no-value-for-parameter
