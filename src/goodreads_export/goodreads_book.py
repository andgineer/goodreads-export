"""Goodreads export CSV parser."""
import re
from typing import List

import markdownify
import pandas as pd

EXPECTED_COLUMNS = {
    "Title",
    "Author",
    "Book Id",
    "My Rating",
    "My Review",
    "Bookshelves",
    "ISBN",
    "ISBN13",
}


class Book:  # pylint: disable=too-few-public-methods,too-many-instance-attributes
    """Extract book description from goodreads export."""

    def __init__(self, goodreads: pd.Series) -> None:
        """Init the object from goodreads export."""
        self.title = goodreads["Title"]
        self.author = goodreads["Author"]
        self.book_id = str(goodreads["Book Id"])
        self.rating = goodreads["My Rating"]
        if isinstance(goodreads["My Review"], str):
            self.review = markdownify.markdownify(goodreads["My Review"])
        else:
            self.review = ""
        self.tags = (
            [f"#book/{shelf.strip()}" for shelf in goodreads["Bookshelves"].split(",")]
            if isinstance(goodreads["Bookshelves"], str)
            else []
        )
        if "#book/book" not in self.tags:
            self.tags.append("#book/book")
        if self.rating is not None and self.rating > 0:
            rating_tag = f"#book/rating{self.rating}"
            if rating_tag not in self.tags:
                self.tags.append(rating_tag)
        self.isbn = goodreads["ISBN"]
        self.isbn13 = goodreads["ISBN13"]
        if series_list_match := re.search(r"\(([^)\n]*)\)", self.title):
            series_match = re.finditer(r"([^#;]*), #\d+(;|$)", series_list_match[1])
            self.series = [series[1].strip() for series in series_match]
        else:
            self.series = []
        self.series_full = [f"{self.author} - {series} - series" for series in self.series]


class GoodreadsBooks(List[Book]):
    """List of books from goodreads export."""

    def __init__(self, csv_file: str) -> None:
        """Load books from goodreads export."""
        books_df = self.load_reviews(csv_file)
        super().__init__([Book(row) for _, row in books_df.iterrows()])

    @staticmethod
    def load_reviews(csv_file: str) -> pd.DataFrame:
        """Load goodreads books info from CSV export."""
        reviews = pd.read_csv(csv_file)
        assert EXPECTED_COLUMNS.issubset(reviews.columns), (
            f"Wrong goodreads export file.\n "
            f"Columns {EXPECTED_COLUMNS - set(reviews.columns)} were not found."
        )
        return reviews
