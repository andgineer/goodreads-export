import json
import os.path
import pathlib
from pathlib import Path
from typing import Optional

import pytest


def _get_repo_root_dir() -> str:
    """
    :return: path to the project folder.
    `tests/` should be in the same folder and this file should be in the root of `tests/`.
    """
    return str(Path(__file__).parent.parent)


ROOT_DIR = _get_repo_root_dir()
RESOURCES = pathlib.Path(f"{ROOT_DIR}/tests/resources")


def normalize_content(content: str) -> str:
    """Normalize content for cross-platform comparison."""
    # Standardize line endings to \n
    normalized = content.replace("\r\n", "\n").replace("\r", "\n")

    # Heuristic for Windows
    # while '\n\n\n' in normalized:
    #     normalized = normalized.replace('\n\n\n', '\n\n')

    return normalized


def paths_content_is_same(path1: Path, path2: Path) -> bool:
    if path1.is_file():
        content1 = normalize_content(path1.open("r", encoding="utf8").read())
        content2 = normalize_content(path2.open("r", encoding="utf8").read())

        assert content1 == content2, (
            f"{path1.parent.name}/{path1.name}"
        )  # with assert we leverage pytest diff
        return True

    subpath_rel_1 = [f"{folder.parent.name}/{folder.name}" for folder in path1.glob("*")]
    subpath_rel_2 = [f"{folder.parent.name}/{folder.name}" for folder in path2.glob("*")]
    assert subpath_rel_1 == subpath_rel_2, set(subpath_rel_1).difference(set(subpath_rel_2))

    for subpath in path1.glob("*"):
        paths_content_is_same(subpath, (path2 / subpath.name))  # do not need result
    return True


class GoodreadsTestCase:
    diff: Optional[list[str]] = None

    def __init__(self, folder: str):
        self.expected_folder = RESOURCES / folder / "books"
        self.merged_folder = RESOURCES / folder / "merged" / "books"
        self.preexisted_folder = RESOURCES / folder / "existed"
        self.csv = RESOURCES / folder / "goodreads_library_export.csv"
        self.meta = json.loads((RESOURCES / folder / "meta.json").read_text(encoding="utf8"))

    def check(self, folder: str, expected_folder: str = None) -> bool:
        if expected_folder is None:
            expected_folder = self.expected_folder
        return paths_content_is_same(Path(expected_folder), Path(folder))

    def copy_existed(self, folder: Path, source: Optional[Path] = None) -> None:
        if source is None:
            source = self.preexisted_folder
        for subpath in source.glob("*"):
            if subpath.is_file():
                (folder / subpath.name).write_text(subpath.read_text())
            else:
                (folder / subpath.name).mkdir()
                self.copy_existed(folder / subpath.name, subpath)


@pytest.fixture(scope="function", params=["create", "update"])
def test_case(request) -> GoodreadsTestCase:
    return GoodreadsTestCase(request.param)


@pytest.fixture(
    scope="function",
    params=[
        "Anna Starobinets.md",
        "Eric Schmidt.md",
        "Liu Cixin.md",
        "Richard P. Feynman.md",
        "Terry Pratchett.md",
        "Theodore Dreiser.md",
    ],
)
def author_markdown(request) -> str:
    with (RESOURCES / "create" / "books" / "authors" / request.param).open(
        "r", encoding="utf8"
    ) as author_file:
        return author_file.read()


@pytest.fixture(
    scope="function",
    params=[
        os.path.join("reviews", "Anna Starobinets - Икарова железа. Книга метаморфоз.md"),
        os.path.join("reviews", "Eric Schmidt - How Google Works.md"),
        os.path.join("reviews", "Liu Cixin - The Wandering Earth.md"),
        os.path.join("reviews", "Terry Pratchett - Mort (Discworld @4; Death @1).md"),
        os.path.join(
            "reviews", "Terry Pratchett - The Light Fantastic (Discworld @2; Rincewind @2).md"
        ),
        os.path.join("reviews", "Theodore Dreiser - The Genius by Theodore Dreiser.md"),
        os.path.join(
            "toread",
            "Richard P. Feynman - Six Not-So-Easy Pieces Einstein's Relativity Symmetry and Space-Time.md",
        ),
    ],
)
def book_markdown(request) -> str:
    with (RESOURCES / "create" / "books" / request.param).open("r", encoding="utf8") as author_file:
        return author_file.read()
