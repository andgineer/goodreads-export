import pytest

from goodreads_export.goodreads_csv_to_markdown import clean_filename


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
