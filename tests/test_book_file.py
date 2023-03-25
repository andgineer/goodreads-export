from pathlib import Path
from unittest.mock import patch

import pytest

import goodreads_export.book_file
from goodreads_export.book_file import BookFile
from goodreads_export.library import Library


def test_book_file_initial_nonbook_content(book_markdown):
    library = Library()
    initial_author = "Author"
    author = library.get_author(name=initial_author)
    initial_content = "Content"
    file_name = "123 - Title - Author.md"
    with pytest.raises(ValueError):
        BookFile(
            library=library,
            file_name=Path(file_name),
            book_id="123",
            title="Title",
            author=author,
            content=initial_content,
        )

    book_file = BookFile(
        library=library,
        file_name=Path(file_name),
        book_id="123",
        title="Title",
        author=author,
        content=book_markdown,
    )
    assert book_file.author.name not in [initial_author, ""]
    assert f"[[{book_file.author.name}]]" in book_markdown


def test_book_file_initial_book_content(book_markdown):
    library = Library()
    initial_author = "Author"
    author = library.get_author(name=initial_author)
    content = book_markdown
    file_name = Path("123 - Title - Author.md")
    book_file = BookFile(
        library=library,
        content=content,
        book_id="123",
        title="Title",
        author=author,
        file_name=file_name,
    )
    assert book_file._file_name == file_name
    assert f"www.goodreads.com/book/show/{book_file.book_id}" in content
    assert f"[{book_file.title}]" in content
    assert f"[[{book_file.author.name}]]: " in content
    assert book_file.file_name == file_name
    assert book_file.content == content
    assert book_file.author.name not in [initial_author, ""]


def test_book_file_defaults_from_content(book_markdown):
    library = Library()
    initial_author = "Author"
    author = library.get_author(name=initial_author)
    initial_content = book_markdown
    file_name = "123 - Title - Author.md"
    book_file = BookFile(
        library=library,
        file_name=Path(file_name),
        content=initial_content,
        title="Title",
        author=author,
    )
    assert f"www.goodreads.com/book/show/{book_file.book_id}" in initial_content
    assert f"[{book_file.title}]" in initial_content
    assert f"[[{book_file.author.name}]]: " in initial_content
    assert str(book_file.file_name) == file_name
    assert book_file.content == initial_content
    assert book_file.author.name != initial_author
    assert f"www.goodreads.com/book/show/{book_file.book_id}" in book_markdown
    assert f"[{book_file.title}]" in book_markdown


def test_book_file_duplicate_name(book_markdown):
    """Test that the file name is changed if the file already exists.

    It should add the book id to the file name.
    """
    initial_author = "Author"
    library = Library()
    author = library.get_author(name=initial_author)
    book_file = BookFile(
        library=library,
        folder=Path(),  # we mock the Path.exists anyway so it does not matter
        author=author,
        content=book_markdown,
        book_id="123",
        title="Title",
    )
    initial_filename = book_file.file_name
    assert book_file.book_id not in str(book_file.file_name)
    with patch.object(goodreads_export.book_file.Path, "exists", return_value=True), patch.object(
        goodreads_export.book_file.Path, "open"
    ):
        book_file.write()
    assert (renamed_filename := book_file.file_name) != initial_filename
    assert book_file.book_id in str(book_file.file_name)
    with patch.object(goodreads_export.book_file.Path, "exists", return_value=True), patch.object(
        goodreads_export.book_file.Path, "open"
    ):
        book_file.write()
    assert book_file.file_name == renamed_filename  # do not add IT int the file name twice


def test_book_file_check():
    initial_author = "Author"
    library = Library()
    author = library.get_author(name=initial_author)
    assert BookFile(
        library=library,
        folder=Path(),  # we mock the Path.exists anyway so it does not matter
        author=author,
        book_id="123",
        title="Title",
    ).check()
