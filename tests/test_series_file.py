from goodreads_export.library import Library
from goodreads_export.series_file import SeriesFile


def test_series_file_check():
    library = Library()
    author = library.author_factory(name="Author")
    assert SeriesFile(library=library, author=author, title="Title").check()
