"""Create md-files from https://www.goodreads.com/ CSV export."""
import os
import sys
from pathlib import Path

import click

from goodreads_export.goodreads_book import GoodreadsBooks
from goodreads_export.library import Library
from goodreads_export.log import Log
from goodreads_export.version import VERSION

GOODREAD_EXPORT_FILE_NAME = "goodreads_library_export.csv"

VERBOSE_OPTION = click.option(
    "--verbose",
    "-v",
    "verbose",
    is_flag=True,
    default=False,
    help="""Increase verbosity.""",
    nargs=1,
)


def merge_authors(log: Log, output_folder: Path) -> Library:
    """Merge authors."""
    books_folder = Library(output_folder, log)
    log.start(f"Reading existing files from {output_folder}")
    print(
        f" loaded {len(books_folder.books)} books, {len(books_folder.authors)} authors, "
        f"skipped {books_folder.stat.skipped_unknown_files} unknown files"
        f" and {books_folder.stat.series_added} series files.",
    )
    books_folder.merge_author_names()
    return books_folder


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
@click.argument(
    "output_folder",
    default=".",
    type=click.Path(exists=True, path_type=Path),
    nargs=1,
)
@VERBOSE_OPTION
@click.option(
    "--in",
    "-i",
    "csv_file",
    default=GOODREAD_EXPORT_FILE_NAME,
    help="""Goodreads export file. By default `goodreads_library_export.csv`.
if you specify just folder it will look for file with this name in that folder.""",
    nargs=1,
)
def import_(verbose: bool, csv_file: str, output_folder: Path) -> None:
    """Convert goodreads export CSV file to markdown files.

    OUTPUT_FOLDER
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

        books_folder = merge_authors(log, output_folder)
        books_folder.dump(books)
        print(
            f"\nAdded {books_folder.stat.books_added} review files, "
            f"{books_folder.stat.authors_added} author files.",
            f"Renamed {books_folder.stat.authors_renamed} authors.",
        )

    except Exception as exc:  # pylint: disable=broad-except
        print(f"\n{exc}")
        sys.exit(1)


@main.command()
@click.argument(
    "output_folder",
    default=".",
    type=click.Path(exists=True, path_type=Path),
    nargs=1,
)
@VERBOSE_OPTION
def check(verbose: bool, output_folder: Path) -> None:
    """Check templates consistency with extraction regexes.

    Loads templates and regexes from OUTPUT_FOLDER/templates.
    To create initial files from embedded default use command `goodreads-export init`.
    """
    try:
        assert output_folder
        log = Log(verbose)
        library = Library()  # we need library without actual folder to run template checks
        library.check_templates()
        log.info("Templates are consistent with extraction regexes.")
    except Exception as exc:  # pylint: disable=broad-except
        print(f"\n{exc}")
        sys.exit(1)


@main.command()
@click.argument(
    "output_folder",
    default=".",
    type=click.Path(exists=True, path_type=Path),
    nargs=1,
)
@VERBOSE_OPTION
def merge(verbose: bool, output_folder: Path) -> None:
    """Merge authors only.

    Use it if you need only re-link to primary author names
    without importing goodreads file.

    OUTPUT_FOLDER
    Folder to merge authors. By default, current folder.

    See https://andgineer.github.io/goodreads-export/ for details.
    """
    try:
        assert output_folder
        log = Log(verbose)
        books_folder = merge_authors(log, output_folder)
        print(
            f"Renamed {books_folder.stat.authors_renamed} authors.",
        )
    except Exception as exc:  # pylint: disable=broad-except
        print(f"\n{exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()  # pylint: disable=no-value-for-parameter
