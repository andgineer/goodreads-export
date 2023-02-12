from pathlib import Path
from unittest.mock import patch

import goodreads_export.book_file
from goodreads_export.book_file import BookFile
from goodreads_export.clean_file_name import clean_file_name
from goodreads_export.templates import Templates


def test_book_file_initial_nonbook_content(book_markdown):
    content = "Content"
    file_name = "123 - Title - Author.md"
    initial_author = "Author"
    book_file = BookFile(
        template=Templates().review,
        book_id="123",
        title="Title",
        folder=Path(),
        author=initial_author,
        file_name=file_name,
        content=content,
    )
    assert book_file.book_id == "123"
    assert book_file.title == "Title"
    assert book_file.author == "Author"
    assert book_file.file_name == file_name
    assert book_file.content == content

    book_file.content = book_markdown
    book_file.parse()
    assert book_file.author != initial_author
    assert f"[[{book_file.author}]]" in book_markdown


def test_book_file_initial_book_content(book_markdown):
    content = book_markdown
    file_name = "123 - Title - Author.md"
    initial_author = "Author"
    book_file = BookFile(
        template=Templates().review,
        content=content,
        book_id="123",
        title="Title",
        folder=Path(),
        author=initial_author,
        file_name=file_name,
    )
    assert f"www.goodreads.com/book/show/{book_file.book_id}" in content
    assert f"[{book_file.title}]" in content
    assert f"[[{book_file.author}]]: " in content
    assert book_file.file_name == file_name
    assert book_file.content == content

    book_file.content = book_markdown
    assert book_file.author != initial_author
    assert f"[[{book_file.author}]]" in book_markdown


def test_book_file_defaults_from_content(book_markdown):
    initial_content = book_markdown
    file_name = "123 - Title - Author.md"
    initial_author = "Author"
    book_file = BookFile(
        template=Templates().review,
        content=initial_content,
        title="Title",
        folder=Path(),
        file_name=file_name,
    )
    assert f"www.goodreads.com/book/show/{book_file.book_id}" in initial_content
    assert f"[{book_file.title}]" in initial_content
    assert f"[[{book_file.author}]]: " in initial_content
    assert book_file.file_name == file_name
    assert book_file.content == initial_content

    book_file.content = book_markdown
    assert book_file.author != initial_author
    assert f"[[{book_file.author}]]" in book_markdown
    assert f"www.goodreads.com/book/show/{book_file.book_id}" in book_markdown
    assert f"[{book_file.title}]" in book_markdown


def test_book_file_defaults_from_class(book_markdown):
    initial_content = "Content"
    title = "Title"
    book_file = BookFile(
        template=Templates().review,
        content=initial_content,
        title=title,
        folder=Path(),
    )
    assert book_file.book_id is None
    assert book_file.title == title
    assert book_file.author is None
    assert book_file._file_name is None
    assert book_file.content == initial_content

    fields = BookFile(
        template=Templates().review, content=book_markdown, title=title, folder=Path()
    )
    book_file.content = book_markdown
    book_file.book_id = fields.book_id
    book_file.author = fields.author
    book_file.review = "Review"
    book_file.rating = 1
    book_file.render()
    assert f"[[{book_file.author}]]" in book_file.content
    assert f"www.goodreads.com/book/show/{book_file.book_id}" in book_file.content
    assert f"[{book_file.title}]" in book_file.content
    assert book_file.file_name == clean_file_name(f"{book_file.author} - {book_file.title}.md")


def test_book_file_duplicate_name(book_markdown):
    book_file = BookFile(
        template=Templates().review,
        content=book_markdown,
        book_id="123",
        title="Title",
        folder=Path(),
    )
    initial_filename = book_file.file_name
    assert book_file.book_id not in book_file.file_name
    with patch.object(goodreads_export.book_file.Path, "exists", return_value=True), patch.object(
        goodreads_export.book_file.Path, "open"
    ):
        book_file.write()
    assert (renamed_filename := book_file.file_name) != initial_filename
    assert book_file.book_id in book_file.file_name
    with patch.object(goodreads_export.book_file.Path, "exists", return_value=True), patch.object(
        goodreads_export.book_file.Path, "open"
    ):
        book_file.write()
    assert book_file.file_name == renamed_filename  # do not add IT int the file name twice


def test_book_file_check():
    assert BookFile.check()
