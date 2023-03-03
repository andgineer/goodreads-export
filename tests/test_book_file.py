from pathlib import Path
from unittest.mock import patch

import goodreads_export.book_file
from goodreads_export.book_file import BookFile
from goodreads_export.clean_file_name import clean_file_name


def test_book_file_initial_nonbook_content(book_markdown):
    initial_content = "Content"
    file_name = "123 - Title - Author.md"
    initial_author = "Author"
    book_file = BookFile(
        file_name=Path(file_name),
        book_id="123",
        title="Title",
        author=initial_author,
        content=initial_content,
    )
    assert book_file.book_id is None  # no book id in content
    assert book_file.title is None  # no title in content
    assert book_file.author is None  # no author in content
    assert str(book_file.file_name) == file_name
    assert book_file.content == initial_content

    book_file.content = book_markdown
    assert book_file.author not in [initial_author, ""]
    assert f"[[{book_file.author}]]" in book_markdown


def test_book_file_initial_book_content(book_markdown):
    content = book_markdown
    file_name = Path("123 - Title - Author.md")
    initial_author = "Author"
    book_file = BookFile(
        content=content,
        book_id="123",
        title="Title",
        author=initial_author,
        file_name=file_name,
    )
    assert book_file._file_name == file_name
    assert f"www.goodreads.com/book/show/{book_file.book_id}" in content
    assert f"[{book_file.title}]" in content
    assert f"[[{book_file.author}]]: " in content
    assert book_file.file_name == file_name
    assert book_file.content == content
    assert book_file.author not in [initial_author, ""]


def test_book_file_defaults_from_content(book_markdown):
    initial_content = book_markdown
    file_name = "123 - Title - Author.md"
    initial_author = "Author"
    book_file = BookFile(
        file_name=Path(file_name),
        content=initial_content,
        title="Title",
        author=initial_author,
    )
    assert f"www.goodreads.com/book/show/{book_file.book_id}" in initial_content
    assert f"[{book_file.title}]" in initial_content
    assert f"[[{book_file.author}]]: " in initial_content
    assert str(book_file.file_name) == file_name
    assert book_file.content == initial_content
    assert book_file.author != initial_author
    assert f"www.goodreads.com/book/show/{book_file.book_id}" in book_markdown
    assert f"[{book_file.title}]" in book_markdown


def test_book_file_defaults_from_class(book_markdown):
    initial_content = "Content"
    initial_author = "Author"
    title = "Title"
    book_file = BookFile(
        content=initial_content,
        title=title,
        author=initial_author,
    )
    assert book_file.book_id is None
    assert book_file.title is None  # no title in initial_content
    assert book_file.author is None  # no author in initial_content
    assert book_file._file_name is None
    assert book_file.content == initial_content

    fields = BookFile(
        content=book_markdown,
        title=title,
        folder=Path(),
        author=initial_author,
    )
    book_file.content = book_markdown
    book_file.book_id = fields.book_id
    book_file.author = fields.author
    book_file.review = "Review"
    book_file.rating = 1
    assert f"[[{book_file.author}]]" in book_file.content
    assert f"www.goodreads.com/book/show/{book_file.book_id}" in book_file.content
    assert f"[{book_file.title}]" in book_file.content
    assert str(book_file.file_name) == clean_file_name(
        f"{book_file.author} - {book_file.title}.md"
    )


def test_book_file_duplicate_name(book_markdown):
    """Test that the file name is changed if the file already exists.

    It should add the book id to the file name.
    """
    author = "Author"
    book_file = BookFile(
        folder=Path(),
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
    assert BookFile.check()
