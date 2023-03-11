from os import mkdir
from pathlib import Path

from click.testing import CliRunner

from goodreads_export.library import Library
from goodreads_export.log import Log


def test_library_load(test_case):
    log = Log()
    runner = CliRunner()
    with runner.isolated_filesystem():
        mkdir("books")
        folder = Path("books")
        test_case.copy_existed(folder)
        books = Library(folder, log)
    assert len(books.books) == len(test_case.meta["existed"]["books"])
    assert sorted(book.title for book in books.books.values()) == sorted(
        [book["title"] for book in test_case.meta["existed"]["books"]]
    )
    assert sorted(book.author.name for book in books.books.values()) == sorted(
        [book["author"] for book in test_case.meta["existed"]["books"]]
    )
    assert sorted(author.name for author in books.authors.values()) == sorted(
        [author["name"] for author in test_case.meta["existed"]["authors"]]
    )


def test_library_merge(test_case):
    log = Log()
    runner = CliRunner()
    with runner.isolated_filesystem():
        mkdir("books")
        folder = Path("books")
        test_case.copy_existed(folder)
        library = Library(folder, log)
        library.merge_author_names()
