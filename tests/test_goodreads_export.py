from os import mkdir

import pytest
from click.testing import CliRunner

from goodreads_export.goodreads_csv_to_markdown import clean_filename, main


@pytest.mark.parametrize(
    "file_name, expected_result",
    [
        ("This is an * example|file_name?.pdf", "This is an x example_file_namepdf"),
        ("This_is_a#file_,%[name]", "This_is_a@file_; percent(name)"),
        ("Invalid/file:\\name", "Invalid_file_name"),
    ],
)
def test_clean_filename(file_name, expected_result):
    """Test that the characters in not_allowed is replaced with spaces."""
    assert clean_filename(file_name) == expected_result


def test_success(test_case):
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("goodreads_library_export.csv", "w") as f:
            f.write(test_case.csv.open("r").read())
        mkdir("books")
        result = runner.invoke(
            main,
            ["-o", "books"],
        )
        assert result.exit_code == 0, f"stdout: {result.output}"
        assert test_case.check("./books"), test_case.diff
