"""Read goodreads export."""
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


def load_reviews(csv_file: str) -> pd.DataFrame:
    """Load goodreads books infor from CSV export."""
    print(f"Loading reviews from {csv_file}...", end="")
    reviews = pd.read_csv(csv_file)
    assert EXPECTED_COLUMNS.issubset(reviews.columns), (
        f"Wrong goodreads export file.\n "
        f"Columns {EXPECTED_COLUMNS - set(reviews.columns)} were not found."
    )
    print(f" loaded {len(reviews)} reviews.")
    return reviews


class Book:  # pylint: disable=too-few-public-methods,too-many-instance-attributes
    """Extract book description from goodreads export."""

    def __init__(self, goodreads: pd.Series) -> None:
        """Init the object from goodreads export."""
        self.title = goodreads["Title"]
        self.author = goodreads["Author"]
        self.book_id = goodreads["Book Id"]
        self.rating = goodreads["My Rating"]
        if isinstance(goodreads["My Review"], str):
            self.review = markdownify.markdownify(goodreads["My Review"])
        else:
            self.review = ""
        if not isinstance(goodreads["Bookshelves"], str):
            self.tags = []
        else:
            self.tags = [f"#book/{shelf.strip()}" for shelf in goodreads["Bookshelves"].split(",")]
        self.isbn = goodreads["ISBN"]
        self.isbn13 = goodreads["ISBN13"]
