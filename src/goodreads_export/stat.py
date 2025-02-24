"""Work statistics."""


class Stat:  # pylint: disable=too-few-public-methods
    """Work statistics."""

    books_added: int = 0
    books_changed: int = 0
    authors_added: int = 0
    skipped_unknown_files: int = 0
    series_added: int = 0
    authors_renamed: int = 0
    unique_authors: set[str] = set()

    def register_author(self, author: str) -> bool:
        """Return True if the author is new."""
        if author not in self.unique_authors:
            self.unique_authors.add(author)
            return True
        return False
