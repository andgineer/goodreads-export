from pathlib import Path
from unittest.mock import patch

import pytest

import goodreads_export.book_file
from goodreads_export.book_file import BookFile, ParseError
from goodreads_export.library import Library


def test_book_file_initial_nonbook_content(book_markdown):
    library = Library()
    initial_author = "Author"
    author = library.author_factory(name=initial_author)
    initial_content = "Content"
    file_name = "123 - Title - Author.md"
    with pytest.raises(ParseError):
        BookFile(
            library=library,
            file_name=Path(file_name),
            book_id="123",
            title="Title",
            author=author,
            content=initial_content,
        )


def test_book_file_content_assign(book_markdown):
    library = Library()
    initial_author = "Author"
    author = library.author_factory(name=initial_author)
    file_name = Path("123 - Title - Author.md")
    book_id = "123"
    title = "Title"
    book_file = BookFile(
        library=library,
        file_name=file_name,
        book_id=book_id,
        title=title,
        author=author,
    )
    book_file.content = book_markdown
    assert book_file.author.name not in [initial_author, ""]
    assert f"[[{book_file.author.file_link}]]" in book_markdown
    assert book_file.book_id != book_id
    assert book_file.title != title
    assert book_file.file_name == file_name


def test_book_file_without_content(book_markdown):
    library = Library()
    initial_author = "Author"
    author = library.author_factory(name=initial_author)
    file_name = Path("123 - Title - Author.md")
    book_id = "123"
    title = "Title"
    book_file = BookFile(
        library=library,
        file_name=file_name,
        book_id=book_id,
        title=title,
        author=author,
    )
    assert book_file.author.name == initial_author
    assert book_file.file_name == file_name
    assert book_file.book_id == book_id
    assert book_file.title == title


def test_book_file_initial_book_content(book_markdown):
    library = Library()
    initial_author = "Author"
    author = library.author_factory(name=initial_author)
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
    assert f"[[{book_file.author.file_link}]]: " in content
    assert book_file.file_name == file_name
    assert book_file.content == content
    assert book_file.author.name not in [initial_author, ""]


def test_book_file_duplicate_name(book_markdown):
    """Test that the file name is changed if the file already exists.

    It should add the book id to the file name.
    """
    initial_author = "Author"
    library = Library()
    author = library.author_factory(name=initial_author)
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
    with (
        patch.object(goodreads_export.book_file.Path, "exists", return_value=True),
        patch.object(goodreads_export.book_file.Path, "open"),
    ):
        book_file.write()
    assert (renamed_filename := book_file.file_name) != initial_filename
    assert book_file.book_id in str(book_file.file_name)
    with (
        patch.object(goodreads_export.book_file.Path, "exists", return_value=True),
        patch.object(goodreads_export.book_file.Path, "open"),
    ):
        book_file.write()
    assert book_file.file_name == renamed_filename  # do not add book_id into the file name twice


def test_book_file_check():
    initial_author = "Author"
    library = Library()
    author = library.author_factory(name=initial_author)
    assert BookFile(
        library=library,
        folder=Path(),  # we mock the Path.exists anyway so it does not matter
        author=author,
        book_id="123",
        title="Title",
    ).check()


def test_review_regex_real_format():
    """Test that review regex can extract review from real production format."""
    from pathlib import Path

    test_file = Path("tests/resources/regex_test/Max Frei - Сказки старого Вильнюса.md")
    assert test_file.exists(), f"Test file not found: {test_file}"

    library = Library()
    author = library.author_factory(name="Max Frei")

    book_file = BookFile(
        library=library,
        folder=test_file.parent,
        file_name=test_file.name,
        content=test_file.read_text(encoding="utf8"),
        author=author,
    )

    # The review should be extracted correctly from the real format
    assert book_file.review is not None, f"Review should not be None, got: {repr(book_file.review)}"
    assert book_file.review.strip() == "Simple review text.", (
        f"Expected 'Simple review text.', got: {repr(book_file.review)}"
    )


def test_review_regex_extraction():
    """Test that review regex can extract review from actual markdown files."""
    from pathlib import Path

    test_file = Path(
        "tests/resources/update/existed/reviews/Pratchett Terry - Mort (Discworld @4; Death @1).md"
    )
    assert test_file.exists(), f"Test file not found: {test_file}"

    # Load the file and parse it
    library = Library()
    author = library.author_factory(name="Pratchett Terry")

    book_file = BookFile(
        library=library,
        folder=test_file.parent,
        file_name=test_file.name,
        content=test_file.read_text(encoding="utf8"),
        author=author,
    )

    # The review should be extracted correctly
    assert book_file.review is not None, "Review should not be None"
    assert book_file.review.strip() == "Fun.", f"Expected 'Fun.', got: {repr(book_file.review)}"


def test_review_regex_multiline_extraction():
    """Review regex should capture multi-line reviews (DOTALL behavior)."""
    library = Library()
    author = library.author_factory(name="Some Author")

    # Compose content similar to default book template with multi-line review
    content = (
        "[[Some Author]]: [Some Title](https://www.goodreads.com/book/show/12345)\n"
        "ISBN123 (ISBN13 456)\n"
        "\n"  # no series links, blank line before review
        "First line of review\n"
        "Second line of review\n"
        "\n"
        "[Search in Calibre](calibre://search/_?q=Some+Title)\n"
    )

    book_file = BookFile(
        library=library,
        folder=Path(),
        file_name=Path("Some Author - Some Title.md"),
        content=content,
        author=author,
    )

    assert book_file.review is not None, "Review should be parsed"
    assert book_file.review.strip() == "First line of review\nSecond line of review", (
        f"Unexpected review: {repr(book_file.review)}"
    )
