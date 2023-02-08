from pathlib import Path

from goodreads_export.author_file import AuthorFile


def test_author_file_initial_nonbook_content(author_markdown):
    content = "Content"
    file_name = "123 - Title - Author.md"
    initial_author = "Author"
    author_file = AuthorFile(
        author=initial_author,
        folder=Path(),
        file_name=file_name,
        content=content,
    )
    assert author_file.author == "Author"
    assert author_file.file_name == file_name
    assert author_file.content == content

    author_file.content = author_markdown
    assert all(f"[{name}]" in author_markdown for name in author_file.names)


def test_author_file_initial_author_content(author_markdown):
    content = author_markdown
    file_name = "123 - Title - Author.md"
    initial_author = "Author"
    author_file = AuthorFile(
        content=content,
        author=initial_author,
        file_name=file_name,
        folder=Path(),
    )
    assert all(f"[{name}]" in author_markdown for name in author_file.names)
    assert author_file.file_name == file_name
    assert author_file.content == content

    author_file.content = author_markdown
    assert all(f"[{name}]" in author_markdown for name in author_file.names)


def test_author_file_defaults_from_content(author_markdown):
    initial_content = author_markdown
    file_name = "123 - Title - Author.md"
    initial_author = "Author"
    author_file = AuthorFile(
        content=initial_content,
        file_name=file_name,
        folder=Path(),
        author=initial_author,
    )
    assert all(f"[{name}]" in author_markdown for name in author_file.names)
    assert author_file.file_name == file_name
    assert author_file.content == initial_content
    assert all(f"[{name}]" in author_markdown for name in author_file.names)

    author_file.content = author_markdown
    assert all(f"[{name}]" in author_markdown for name in author_file.names)


def test_author_file_defaults_from_class(author_markdown):
    initial_author = "Author"
    author_file = AuthorFile(
        author=initial_author,
        folder=Path(),
    )
    assert author_file.author == initial_author
    assert author_file._file_name is None
    assert (
        author_file.content
        == "[Author](https://www.goodreads.com/search?utf8=%E2%9C%93&q=Author&search_type=books&search%5Bfield%5D=author)\n\n#book/author\n"
    )
    assert author_file.names == ["Author"]

    author_file.content = author_markdown
    author_file.parse()
    assert author_file.content == author_markdown
    assert all(f"[{name}]" in author_markdown for name in author_file.names)


def test_author_check():
    assert AuthorFile.check()
