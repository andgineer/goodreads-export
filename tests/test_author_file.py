from pathlib import Path

import pytest

from goodreads_export.author_file import AuthorFile
from goodreads_export.data_file import ParseError
from goodreads_export.library import Library


def test_author_file_initial_nonbook_content(author_markdown):
    library = Library()
    content = "Content"
    file_name = "123 - Title - Author.md"
    initial_author = "Author"
    with pytest.raises(ParseError):
        AuthorFile(
            library=library,
            name=initial_author,
            file_name=Path(file_name),
            content=content,
        )


def are_names_in_content(author_file, author_markdown):
    assert all(
        f"[{name}]" in author_markdown for name in author_file.names
    ), f"Not all {author_file.names} are in {author_markdown}"
    assert author_file.name == author_file.names[0]


def test_author_file_initial_author_content(author_markdown):
    library = Library()
    content = author_markdown
    file_name = "123 - Title - Author.md"
    initial_author = "Author"
    author_file = AuthorFile(
        library=library,
        content=content,
        name=initial_author,
        file_name=Path(file_name),
    )
    assert all(f"[{name}]" in author_markdown for name in author_file.names)
    assert str(author_file.file_name) == file_name
    assert author_file.content == content

    author_file.content = author_markdown
    are_names_in_content(author_file, author_markdown)


def test_author_file_defaults_from_content(author_markdown):
    library = Library()
    initial_content = author_markdown
    file_name = "123 - Title - Author.md"
    initial_author = "Author"
    author_file = AuthorFile(
        library=library,
        content=initial_content,
        file_name=Path(file_name),
        name=initial_author,
    )
    assert all(f"[{name}]" in author_markdown for name in author_file.names)
    assert str(author_file.file_name) == file_name
    assert author_file.content == initial_content
    assert all(f"[{name}]" in author_markdown for name in author_file.names)

    author_file.content = author_markdown
    are_names_in_content(author_file, author_markdown)


def test_author_file_defaults_from_class(author_markdown):
    library = Library()
    initial_author = "Author"
    author_file = AuthorFile(
        library=library,
        name=initial_author,
    )
    assert author_file.name == initial_author
    assert author_file._file_name is None
    assert (
        author_file.content
        == "[Author](https://www.goodreads.com/search?utf8=%E2%9C%93&q=Author&search_type=books&search%5Bfield%5D=author)\n\n#book/author\n"
    )
    assert author_file.names == [initial_author]

    author_file.content = author_markdown
    assert author_file.content == author_markdown
    are_names_in_content(author_file, author_markdown)


def test_author_file_init_without_content(author_markdown):
    library = Library()
    file_name = "123 - Title - Author.md"
    initial_author = "Author"
    author_file = AuthorFile(
        library=library,
        name=initial_author,
        file_name=Path(file_name),
    )
    assert author_file.name == initial_author
    assert author_file.file_name == Path(file_name)
    assert author_file.content == (
        f"[{initial_author}](https://www.goodreads.com/search?utf8=%E2%9C%93"
        f"&q={initial_author}&search_type=books&search%5Bfield%5D=author)\n\n#book/author\n"
    )
    assert author_file.names == ["Author"]

    author_file.content = author_markdown
    are_names_in_content(author_file, author_markdown)


def test_author_check():
    library = Library()
    assert AuthorFile(library=library, name="Author").check()
