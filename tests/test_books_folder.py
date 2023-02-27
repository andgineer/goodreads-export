from os import mkdir
from pathlib import Path

from click.testing import CliRunner

from goodreads_export.books_folder import BooksFolder
from goodreads_export.log import Log


def test_books_folder_load(test_case):
    log = Log()
    runner = CliRunner()
    with runner.isolated_filesystem():
        mkdir("books")
        folder = Path("books")
        test_case.copy_existed(folder)
        books = BooksFolder(folder, log)
    assert len(books.books) == len(test_case.meta["existed"]["books"])
    assert [book.title for book in books.books.values()] == [
        book["title"] for book in test_case.meta["existed"]["books"]
    ]
    assert [book.author for book in books.books.values()] == [
        book["author"] for book in test_case.meta["existed"]["books"]
    ]
    assert [author.name for author in books.authors.values()] == [
        author["name"] for author in test_case.meta["existed"]["authors"]
    ]


def test_books_folder_merge(test_case):
    log = Log()
    runner = CliRunner()
    with runner.isolated_filesystem():
        mkdir("books")
        folder = Path("books")
        test_case.copy_existed(folder)
        books = BooksFolder(folder, log)
        books.merge_author_names()
