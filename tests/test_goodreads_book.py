from os import mkdir

import pytest
from click.testing import CliRunner

from goodreads_export.main import main
from goodreads_export.markdown_book import clean_file_name


@pytest.mark.parametrize(
    "file_name, expected_result",
    [
        ("This is an * example|file_name?.pdf", "This is an x example_file_name.pdf"),
        ("This_is_a#file_,%[name]", "This_is_a@file_ percent(name)"),
        ("Invalid/file:\\name", "Invalid_file_name"),
    ],
)
def test_clean_filename(file_name, expected_result):
    """Test that the characters in not_allowed is replaced with spaces."""
    assert clean_file_name(file_name) == expected_result


def test_success(test_case):
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("goodreads_library_export.csv", "w", encoding="utf8") as f:
            f.write(test_case.csv.open("r", encoding="utf8").read())
        mkdir("books")
        # todo copy from test_case.books_folder to books
        result = runner.invoke(
            main,
            ["-o", "books"],
        )
        assert result.exit_code == 0, f"stdout: {result.output}"
        assert test_case.check("./books"), test_case.diff
