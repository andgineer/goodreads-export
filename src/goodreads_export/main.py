"""Command line interface."""

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

import rich_click as click
from platformdirs import user_config_dir

from goodreads_export.goodreads_book import GoodreadsBooks
from goodreads_export.library import Library
from goodreads_export.log import Log
from goodreads_export.template_metadata import (
    compute_content_hash,
    compute_file_hash,
    load_metadata,
    save_metadata,
    update_metadata,
)
from goodreads_export.templates import (
    DEFAULT_BUILTIN_TEMPLATE,
    TEMPLATE_FILES,
    TemplateSet,
    TemplatesLoader,
)
from goodreads_export.version import VERSION

GOODREAD_EXPORT_FILE_NAME = "goodreads_library_export.csv"
DEFAULT_TEMPLATES_FOLDER = "./templates"


@dataclass
class ConfigureReport:
    """Report of configure operation."""

    created_files: list[str] = field(default_factory=list)
    updated_files: list[str] = field(default_factory=list)
    new_versions: list[str] = field(default_factory=list)
    unchanged_files: list[str] = field(default_factory=list)

    def is_empty(self) -> bool:
        """Check if any changes were made."""
        return not (self.created_files or self.updated_files or self.new_versions)


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
    help=f"""Folder with templates. If not absolute it's relative to `BOOKS_FOLDER`.
If not specified, look for `{DEFAULT_TEMPLATES_FOLDER}` in `BOOKS_FOLDER`.
If not found use built-in templates, see `--builtin-name`.
DEPRECATED: Use --config/-c instead.""",
    nargs=1,
)

CONFIG_OPTION = click.option(
    "--config",
    "-c",
    "config_folder",
    default=None,
    type=click.Path(path_type=Path),
    help=(
        "Config folder for templates. "
        "If not specified, look for templates in BOOKS_FOLDER or use built-in."
    ),
    nargs=1,
)

BUILTIN_TEMPLATES_NAME_OPTION = click.option(
    "--builtin-name",
    "-b",
    "builtin_name",
    default=None,
    help=f"""Name of the built-in template. Use `{DEFAULT_BUILTIN_TEMPLATE}` if not specified.""",
    nargs=1,
)


BOOKS_FOLDER_OPTION = click.argument(
    "books_folder",
    type=click.Path(exists=True, path_type=Path),
    nargs=1,
)


BOOKS_FOLDER_OPTIONAL_OPTION = click.argument(
    "books_folder",
    required=False,
    type=click.Path(exists=True, path_type=Path),
    nargs=1,
)


def merge_authors(log: Log, books_folder: Path, templates: TemplateSet) -> Library:
    """Load library and merge authors."""
    library = load_library(log=log, books_folder=books_folder, templates=templates)
    library.merge_author_names()
    return library


def load_library(log: Log, books_folder: Path, templates: TemplateSet) -> Library:
    """Load library."""
    library = Library(folder=books_folder, log=log, templates=templates)
    log.start(f"Reading existing files from {books_folder}")
    print(
        f" loaded {len(library.books)} books, {len(library.authors)} authors"
        f" and {library.stat.series_added} series files."
        f" Skipped {library.stat.skipped_unknown_files} unknown files",
    )
    return library


def resolve_config_folder(config_folder: Path | None) -> Path:
    """Resolve config folder path for templates.

    Args:
        config_folder: User-specified config folder or None.

    Returns:
        Resolved config folder path.

    Raises:
        ValueError: If relative path provided without books_folder.
    """
    if config_folder is None:
        # Use default app config directory
        config_folder = Path(user_config_dir("goodreads-export")) / "templates"
    elif not config_folder.is_absolute():
        raise ValueError("Config folder must be absolute path")

    # Create directory if it doesn't exist
    config_folder.mkdir(parents=True, exist_ok=True)

    return config_folder


def resolve_builtin_name(
    templates_folder: Path,
    requested_builtin_name: str | None,
    force: bool,
    log: Log,
) -> str:
    """Resolve which builtin template set to use.

    Args:
        templates_folder: Path to templates folder.
        requested_builtin_name: User-requested builtin name or None.
        force: Whether force flag is set.
        log: Log instance.

    Returns:
        Builtin name to use.

    Raises:
        ValueError: If switching template sets without --force.
    """
    metadata = load_metadata(templates_folder)
    templates_exist = any((templates_folder / f).exists() for f in TEMPLATE_FILES)

    if not templates_exist:
        # First run - use requested or default
        return requested_builtin_name or DEFAULT_BUILTIN_TEMPLATE

    if not metadata:
        # Templates exist but no metadata - use requested or default
        log.warning("Templates exist but metadata is missing. Using requested or default.")
        return requested_builtin_name or DEFAULT_BUILTIN_TEMPLATE

    saved_builtin_name = metadata.get("builtin_name")

    if requested_builtin_name is None:
        # No name specified - use saved one
        return saved_builtin_name or DEFAULT_BUILTIN_TEMPLATE

    if requested_builtin_name == saved_builtin_name:
        # Same as saved - use it
        return requested_builtin_name

    # Different from saved - require --force
    if not force:
        raise ValueError(
            f"Existing templates were created from '{saved_builtin_name}' template set.\n"
            f"You specified '{requested_builtin_name}' template set which is different.\n\n"
            f"If you want to replace all templates with files from "
            f"'{requested_builtin_name}' template set,\n"
            f"use --force/-f flag. WARNING: This will overwrite all your customizations\n"
            f"in template files if you made any.\n\n"
            f"Run: goodreads-export configure --builtin-name {requested_builtin_name} --force",
        )

    # Force is set - allow switching
    log.warning(
        f"Switching template set from '{saved_builtin_name}' to '{requested_builtin_name}'.\n"
        f"All template files will be replaced. User modifications will be lost.",
    )
    return requested_builtin_name


def detect_user_modifications(
    templates_folder: Path,
    metadata: dict | None,
    force: bool,
) -> dict[str, bool]:
    """Detect which template files were modified by user.

    Args:
        templates_folder: Path to templates folder.
        metadata: Template metadata or None.
        force: Whether force flag is set (all files considered unmodified).

    Returns:
        Dictionary mapping file_name -> is_modified.
    """
    if force:
        # Force mode - all files considered unmodified
        return dict.fromkeys(TEMPLATE_FILES, False)

    if not metadata:
        # If metadata doesn't exist, assume all files are new (not modified)
        return dict.fromkeys(TEMPLATE_FILES, False)

    modifications = {}

    # Compare with stored hashes
    for file_name in TEMPLATE_FILES:
        file_path = templates_folder / file_name
        if not file_path.exists():
            modifications[file_name] = False  # File doesn't exist, will be created
            continue

        stored_hash = metadata["files"].get(file_name, {}).get("hash")
        if stored_hash:
            current_hash = compute_file_hash(file_path)
            modifications[file_name] = current_hash != stored_hash
        else:
            modifications[file_name] = False  # New file, not modified yet

    return modifications


def configure_templates(  # noqa: PLR0913
    templates_folder: Path,
    builtin_name: str,
    modifications: dict[str, bool],
    metadata: dict | None,
    force: bool,
) -> ConfigureReport:
    """Create or update templates based on modification status.

    Args:
        templates_folder: Path to templates folder.
        builtin_name: Name of builtin template set to use.
        modifications: Dictionary mapping file_name -> is_modified.
        metadata: Template metadata or None.
        force: Whether force flag is set.

    Returns:
        ConfigureReport with operation results.
    """
    report = ConfigureReport()
    builtin_hashes = {}

    # Compute hashes of built-in templates
    for file_name in TEMPLATE_FILES:
        builtin_content = TemplatesLoader.get_builtin_file_content(builtin_name, file_name)
        builtin_hashes[file_name] = compute_content_hash(builtin_content)

    for file_name in TEMPLATE_FILES:
        file_path = templates_folder / file_name
        builtin_content = TemplatesLoader.get_builtin_file_content(builtin_name, file_name)
        builtin_hash = builtin_hashes[file_name]

        if not file_path.exists():
            # File doesn't exist - create it
            file_path.write_text(builtin_content, encoding="utf-8")
            report.created_files.append(file_name)
        elif force or not modifications[file_name]:
            # Force mode or file not modified - update directly
            # Check if built-in template actually changed
            stored_hash = metadata["files"].get(file_name, {}).get("hash") if metadata else None
            if stored_hash != builtin_hash or force:
                file_path.write_text(builtin_content, encoding="utf-8")
                report.updated_files.append(file_name)
            else:
                report.unchanged_files.append(file_name)
        else:
            # File modified and not force - create .latest version only if built-in changed
            stored_hash = metadata["files"].get(file_name, {}).get("hash") if metadata else None
            if stored_hash != builtin_hash:
                latest_file_path = templates_folder / f"{file_name}.latest"
                latest_file_path.write_text(builtin_content, encoding="utf-8")
                report.new_versions.append(file_name)
            # Original file remains unchanged

    return report


def format_configure_report(
    report: ConfigureReport,
    templates_folder: Path,
) -> str:
    """Format configure operation report.

    Args:
        report: ConfigureReport instance.
        templates_folder: Path to templates folder.

    Returns:
        Formatted report string.
    """
    lines = [f"Configuring templates in {templates_folder}...", ""]

    if report.created_files:
        lines.append("Created files (first run):")
        for file_name in report.created_files:
            lines.append(f"  ✓ {file_name}")
        lines.append("")
        lines.append("Configuration completed. Metadata created.")
        return "\n".join(lines)

    if report.is_empty():
        lines.append("All templates are up to date. No changes needed.")
        return "\n".join(lines)

    if report.updated_files:
        lines.append("Updated files (user did not modify):")
        for file_name in report.updated_files:
            lines.append(f"  ✓ {file_name}")
        lines.append("")

    if report.new_versions:
        lines.append("New versions created (user modified these files):")
        for file_name in report.new_versions:
            lines.append(f"  → {file_name}.latest (new version available)")
        lines.append("")
        lines.append("To apply new versions, review and rename:")
        for file_name in report.new_versions:
            lines.append(f"  mv {file_name}.latest {file_name}")
        lines.append("")

    if report.unchanged_files:
        lines.append(f"Unchanged files: {len(report.unchanged_files)}")

    lines.append("Configuration completed. Metadata updated.")
    return "\n".join(lines)


def load_templates(
    log: Log,
    books_folder: Path | None,
    templates_folder: Path | None,
    builtin_templates_name: str | None,
) -> TemplateSet:
    """Load templates.

    If templates_folder is not None, load from this folder.

    Otherwise, load embedded templated with specified or default name.
    If default templates folder exists in the books_folder, and builtin_name is not None,
    load the built-in and notify that we ignore existed template folder.

    If built-in explicitly specified, silently ignore the default templates folder.
    """
    if builtin_templates_name is not None and templates_folder is not None:
        log.error("You can't specify both `--builtin-name` and `--templates-folder` or `--config`.")
        sys.exit(1)
    try:
        if templates_folder is None:
            if books_folder is not None and (books_folder / DEFAULT_TEMPLATES_FOLDER).is_dir():
                if builtin_templates_name is None:
                    return TemplatesLoader().load_folder(
                        books_folder / DEFAULT_TEMPLATES_FOLDER,
                    )
                log.info(
                    f"Using embedded templates `{builtin_templates_name}, "
                    f"ignore templates in `{DEFAULT_TEMPLATES_FOLDER}`.",
                )
                return TemplatesLoader().load_builtin(builtin_templates_name)
            if builtin_templates_name is None:
                return TemplatesLoader().load_builtin()
        elif not templates_folder.is_absolute():
            if books_folder is None:
                raise ValueError(
                    "if template folder is relative, need books folder to build its full path.",
                )
            templates_folder = books_folder / templates_folder
        if builtin_templates_name is not None:
            return TemplatesLoader().load_builtin(builtin_templates_name)
        return TemplatesLoader().load_folder(
            templates_folder,  # type: ignore  # mypy bug, see templates_folder check above
        )
    except Exception as exc:  # noqa: BLE001
        log.error(f"Error loading templates: {exc}")
        sys.exit(1)


@click.group(invoke_without_command=True)
@click.version_option(version=VERSION, prog_name="goodreads-export")
@click.pass_context
def main(ctx: click.Context) -> None:
    """Create markdown files from https://www.goodreads.com/ CSV export.

    Documentation https://andgineer.github.io/goodreads-export/en/

    To see help on the commands use `goodreads-export COMMAND --help`.
    For example: `goodreads-export import --help`.
    """
    try:
        if not ctx.invoked_subcommand:
            click.echo("Error: Missing command.")
            click.echo(main.get_help(ctx))
            sys.exit(1)
    except Exception as exc:  # noqa: BLE001
        print(f"\n{exc}")
        sys.exit(1)


@main.command(name="import")
@BOOKS_FOLDER_OPTION
@VERBOSE_OPTION
@CONFIG_OPTION
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
def import_(  # noqa: PLR0913
    verbose: bool,
    csv_file: str,
    books_folder: Path,
    config_folder: Path | None,
    templates_folder: Path | None,
    builtin_name: str | None,
) -> None:
    """Convert goodreads export CSV file to markdown files.

    BOOKS_FOLDER
    Folder where we put result. Do not change existed files except authors merge if necessary.

    See details in https://andgineer.github.io/goodreads-export/en/
    """
    try:
        log = Log(verbose)

        if os.path.isdir(
            csv_file,
        ):  # if folder as csv_file try to find goodreads file in that folder
            csv_file = os.path.join(csv_file, GOODREAD_EXPORT_FILE_NAME)
        if not os.path.isfile(csv_file):
            print(f"Goodreads export file '{csv_file}' not found.")
            sys.exit(1)
        log.start(f"Loading reviews from {csv_file}")
        books = GoodreadsBooks(csv_file)
        print(f" loaded {len(books)} reviews.")
        # Use config_folder if provided, otherwise fall back to templates_folder
        templates_path = config_folder if config_folder is not None else templates_folder
        library = merge_authors(
            log=log,
            books_folder=books_folder,
            templates=load_templates(log, books_folder, templates_path, builtin_name),
        )
        library.dump(books)
        print(
            f"\nAdded {library.stat.books_added} review files, "
            f"changed {library.stat.books_changed} review files, "
            f"{library.stat.authors_added} author files.",
            f"Renamed {library.stat.authors_renamed} authors.",
        )
    except Exception as exc:  # noqa: BLE001
        print(f"\n{exc}")
        sys.exit(1)


@main.command()
@BOOKS_FOLDER_OPTIONAL_OPTION
@VERBOSE_OPTION
@CONFIG_OPTION
@TEMPLATES_FOLDER_OPTION
@BUILTIN_TEMPLATES_NAME_OPTION
def check(
    verbose: bool,
    books_folder: Path | None,
    config_folder: Path | None,
    templates_folder: Path | None,
    builtin_name: str | None,
) -> None:
    """Check templates consistency with extraction regexes.

    BOOKS_FOLDER
    Optional books' folder. Test loading books from the folder if specified.
    Also used as root if `--templates-folder` is relative.
    """
    try:
        log = Log(verbose)
        # Use config_folder if provided, otherwise fall back to templates_folder
        templates_path = config_folder if config_folder is not None else templates_folder
        templates = load_templates(log, books_folder, templates_path, builtin_name)
        library = Library(  # no `folder` argument: for template checks do not want changes in fs
            log=log,
            templates=templates,
        )
        library.check_templates()
        log.info("Templates are consistent with extraction regexes.")
        if books_folder is not None:
            load_library(log=log, books_folder=books_folder, templates=templates)
    except Exception as exc:  # noqa: BLE001
        print(f"\n{exc}")
        sys.exit(1)


@main.command()
@BOOKS_FOLDER_OPTION
@VERBOSE_OPTION
@CONFIG_OPTION
@TEMPLATES_FOLDER_OPTION
@BUILTIN_TEMPLATES_NAME_OPTION
def merge(
    verbose: bool,
    books_folder: Path,
    config_folder: Path | None,
    templates_folder: Path | None,
    builtin_name: str | None,
) -> None:
    """Merge authors in the `BOOKS_FOLDER`.

    Unlike `import` do not need goodreads file.

    See https://andgineer.github.io/goodreads-export/en/ for details.
    """
    try:
        log = Log(verbose)
        # Use config_folder if provided, otherwise fall back to templates_folder
        templates_path = config_folder if config_folder is not None else templates_folder
        library = merge_authors(
            log=log,
            books_folder=books_folder,
            templates=load_templates(log, books_folder, templates_path, builtin_name),
        )
        print(
            f"Renamed {library.stat.authors_renamed} authors.",
        )
    except Exception as exc:  # noqa: BLE001
        print(f"\n{exc}")
        sys.exit(1)


@main.command()
@VERBOSE_OPTION
@click.option(
    "--config",
    "-c",
    "config_folder",
    default=None,
    type=click.Path(path_type=Path),
    help="Config folder for templates. If not specified, use default app config directory.",
    nargs=1,
)
@BUILTIN_TEMPLATES_NAME_OPTION
@click.option(
    "--force",
    "-f",
    "force",
    is_flag=True,
    default=False,
    help="Force update: always replace templates with new versions, even if user modified them.",
)
def configure(
    verbose: bool,
    config_folder: Path | None,
    builtin_name: str | None,
    force: bool,
) -> None:
    """Create or update config, preserving user templates modifications.

    Creates templates in app config directory if they don't exist.
    Updates templates that user did not modify.
    For modified templates, creates new version files with .latest extension.

    See https://andgineer.github.io/goodreads-export/en/ for details.
    """
    try:
        log = Log(verbose)

        # Resolve config folder
        templates_folder = resolve_config_folder(config_folder)

        # Resolve builtin name
        builtin_name = resolve_builtin_name(templates_folder, builtin_name, force, log)

        # Load metadata
        metadata = load_metadata(templates_folder)

        # Detect user modifications
        modifications = detect_user_modifications(templates_folder, metadata, force)

        # Configure templates
        report = configure_templates(
            templates_folder,
            builtin_name,
            modifications,
            metadata,
            force,
        )

        # Update metadata
        updated_metadata = update_metadata(templates_folder, builtin_name)
        save_metadata(templates_folder, updated_metadata)

        # Print report
        print(format_configure_report(report, templates_folder))

    except Exception as exc:  # noqa: BLE001
        print(f"\n{exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()  # pylint: disable=no-value-for-parameter
