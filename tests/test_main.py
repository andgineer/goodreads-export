import os
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

import goodreads_export.main
from goodreads_export.log import Log
from goodreads_export.main import DEFAULT_TEMPLATES_FOLDER, load_templates, main
from goodreads_export.templates import TemplatesLoader
from goodreads_export.version import VERSION


def test_main_version():
    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "--version",
        ],
    )
    assert result.exit_code == 0, f"stdout: {result.output}"
    assert VERSION in result.output


def test_main_wrong_csv():
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("goodreads_library_export.csv", "w") as f:
            f.write("-fake-")
        result = runner.invoke(
            main,
            ["import", "."],
        )
    assert result.exit_code == 1, f"stdout: {result.output}"
    assert "Wrong goodreads export file" in result.output
    assert "Book Id" in result.output
    assert "Author" in result.output


def test_main_wrong_columns():
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("goodreads_library_export.csv", "w") as f:
            f.write("Author,Fake")
        result = runner.invoke(
            main,
            ["import", "."],
        )
    assert result.exit_code == 1, f"stdout: {result.output}"
    assert "Wrong goodreads export file" in result.output
    assert "Book Id" in result.output
    assert "Author" not in result.output


def test_main_wrong_folder_csv():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            main,
            ["import", ".", "-i", "."],
        )
    assert result.exit_code == 1, f"stdout: {result.output}"
    assert "not found" in result.output


def test_main_no_csv():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            main,
            ["import", ".", "-i", "fake"],
        )
    assert result.exit_code == 1, f"stdout: {result.output}"
    assert "not found" in result.output


def test_main_merge():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            main,
            ["merge", "."],
        )
    assert result.exit_code == 0, f"stdout: {result.output}"
    assert "loaded 0 books, 0 authors, skipped 0 unknown files" in result.output


def test_main_verbose(test_case):
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("goodreads_library_export.csv", "w", encoding="utf8") as f:
            f.write(test_case.csv.open("r", encoding="utf8").read())
        result = runner.invoke(
            main,
            ["import", ".", "--verbose"],
        )
    assert result.exit_code == 0, f"stdout: {result.output}"
    assert "loaded 0 books, 0 authors, skipped 0 unknown files" in result.output
    assert "Saved book" in result.output


def test_main_check():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            main,
            ["check"],
        )
    assert result.exit_code == 0, f"stdout: {result.output}"
    assert "Templates are consistent" in result.output


def test_load_templates_both_path_and_folder():
    runner = CliRunner()
    with runner.isolated_filesystem():
        with patch("goodreads_export.main.TemplatesLoader") as mock_templates:
            with pytest.raises(SystemExit) as exc:
                load_templates(
                    log=Log(),
                    books_folder=Path("books"),
                    templates_folder=Path("templates"),
                    builtin_templates_name="default",
                )
                assert mock_templates.call_count == 0
                assert "both" in str(exc.value)


def test_load_templates_default_embedded():
    runner = CliRunner()
    with runner.isolated_filesystem():
        with patch.object(
            goodreads_export.main.TemplatesLoader, "load_builtin"
        ) as mock_load_templates:
            load_templates(
                log=Log(),
                books_folder=Path("books"),
                templates_folder=None,
                builtin_templates_name=None,
            )
            mock_load_templates.assert_called_with()


def test_load_templates_default_folder_exists():
    runner = CliRunner()
    with runner.isolated_filesystem():
        with patch.object(
            goodreads_export.main.TemplatesLoader, "load_folder"
        ) as mock_load_templates:
            books_folder = Path("books")
            templates_folder = books_folder / DEFAULT_TEMPLATES_FOLDER
            os.makedirs(templates_folder)
            load_templates(
                log=Log(),
                books_folder=books_folder,
                templates_folder=None,
                builtin_templates_name=None,
            )
            mock_load_templates.assert_called_with(templates_folder)


def test_load_templates_abs_folder():
    runner = CliRunner()
    with runner.isolated_filesystem():
        with patch.object(
            goodreads_export.main.TemplatesLoader, "load_folder"
        ) as mock_load_templates:
            books_folder = Path("books")
            templates_folder = Path("/templates")
            load_templates(
                log=Log(),
                books_folder=books_folder,
                templates_folder=templates_folder,
                builtin_templates_name=None,
            )
            mock_load_templates.assert_called_with(templates_folder)


def test_load_templates_rel_folder():
    runner = CliRunner()
    with runner.isolated_filesystem():
        with patch.object(
            goodreads_export.main.TemplatesLoader, "load_folder"
        ) as mock_load_templates:
            books_folder = Path("books")
            templates_folder = Path("templates")
            load_templates(
                log=Log(),
                books_folder=books_folder,
                templates_folder=templates_folder,
                builtin_templates_name=None,
            )
            mock_load_templates.assert_called_with(books_folder / templates_folder)


def test_load_templates_embedded_name():
    runner = CliRunner()
    with runner.isolated_filesystem():
        with patch.object(
            goodreads_export.main.TemplatesLoader, "load_builtin"
        ) as mock_load_templates:
            templates_name = "some_name"
            load_templates(
                log=Log(),
                books_folder=Path("books"),
                templates_folder=None,
                builtin_templates_name=templates_name,
            )
            mock_load_templates.assert_called_with(templates_name)


def test_main_init():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            main,
            ["init", "."],
        )
        assert result.exit_code == 0, f"stdout: {result.output}"
        templates_folder = Path(DEFAULT_TEMPLATES_FOLDER)
        assert templates_folder.is_dir()
        builtin_folder = TemplatesLoader.builtin_folder("default")
        for file in builtin_folder.iterdir():
            assert file.read_text() == (templates_folder / file.name).read_text()
        assert {file.name for file in builtin_folder.iterdir()} == {
            file.name for file in templates_folder.iterdir()
        }
