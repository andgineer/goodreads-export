from click.testing import CliRunner

from goodreads_export.main import main
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
            ["import"],
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
            ["import"],
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
            ["import", "-i", "."],
        )
    assert result.exit_code == 1, f"stdout: {result.output}"
    assert "not found" in result.output


def test_main_no_csv():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            main,
            ["import", "-i", "fake"],
        )
    assert result.exit_code == 1, f"stdout: {result.output}"
    assert "not found" in result.output


def test_main_merge():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            main,
            ["import", "--merge"],
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
            ["--verbose", "import"],
        )
    assert result.exit_code == 0, f"stdout: {result.output}"
    assert "loaded 0 books, 0 authors, skipped 0 unknown files" in result.output
    assert "Added review" in result.output
