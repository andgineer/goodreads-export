"""Load existed md files."""
import glob
import re
from pathlib import Path

import pandas as pd


def load_reviews(folder: str) -> pd.DataFrame:
    """Load existed book reviews.

    Look for goodreads book ID inside files.
    """
    columns = ["File Path", "File Name", "Title", "My Review", "Book Id"]
    reviews_dfs = []
    for filename in glob.glob(f"{folder}/*.md"):
        with open(filename, "r", encoding="utf8") as review_file:
            reviews_dfs.append(
                pd.DataFrame(
                    [
                        [
                            filename,
                            Path(filename).stem,
                            None,
                            review_file.read(),
                            None,
                        ]
                    ],
                    columns=columns,
                )
            )
    reviews_df = pd.concat(reviews_dfs, axis=0)
    for _, row in reviews_df.iterrows():
        if "-" in row["Title"]:
            row["Title"] = row["Title"].split("-")[1].strip()
        if id_match := re.search(
            r"\[([^[]*)\]\(https://www.goodreads.com/book/show/(\d+)", row["My Review"]
        ):
            row["Book Id"] = id_match[2]
            row["Title"] = id_match[1]
    return reviews_df


def load_authors(folder: str) -> pd.DataFrame:
    """Load existed authors.

    Look for author synonyms inside files.
    """
    columns = ["File Path", "File Name", "Author", "Author Page"]
    authors_dfs = []
    for filename in glob.glob(f"{folder}/*.md"):
        with open(filename, "r", encoding="utf8") as author_file:
            authors_dfs.append(
                pd.DataFrame(
                    [[filename, Path(filename).stem, None, author_file.read()]],
                    columns=columns,
                )
            )
    authors_df = pd.concat(authors_dfs, axis=0)
    for _, row in authors_df.iterrows():
        if id_match := re.search(
            (
                r"\[([^]]*)\]\(https://www.goodreads.com/search?utf8=%E2%9C%93&q=([^)]*)"
                r"&search_type=books&search%5Bfield%5D=author)\)"
            ),
            row["Author Page"],
        ):
            # todo add all synonyms to search index?
            row["Author"] = id_match[1]
    return authors_df
