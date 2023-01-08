from click.testing import CliRunner

from goodreads_export.goodreads_csv_to_markdown import main
from goodreads_export.version import VERSION


def test_main_version():
    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "--version",
        ],
    )
    assert result.exit_code == 0
    assert VERSION in result.output
