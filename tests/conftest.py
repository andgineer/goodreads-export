import pathlib
from pathlib import Path
from typing import List, Optional

import pytest


def _get_repo_root_dir() -> str:
    """
    :return: path to the project folder.
    `tests/` should be in the same folder and this file should be in the root of `tests/`.
    """
    return str(Path(__file__).parent.parent)


ROOT_DIR = _get_repo_root_dir()
RESOURCES = pathlib.Path(f"{ROOT_DIR}/tests/resources")


def paths_content_is_same(path1: Path, path2: Path) -> bool:
    if path1.is_file():
        assert (
            path1.open("r", encoding="utf8").read()
            == path2.open("r", encoding="utf8").read()  # with assert we leverage pytest diff
        ), f"{path1.parent.name}/{path1.name}"
        return True

    subpath_rel_1 = [f"{folder.parent.name}/{folder.name}" for folder in path1.glob("*")]
    subpath_rel_2 = [f"{folder.parent.name}/{folder.name}" for folder in path2.glob("*")]
    assert subpath_rel_1 == subpath_rel_2, set(subpath_rel_1).difference(set(subpath_rel_2))

    for subpath in path1.glob("*"):
        paths_content_is_same(subpath, (path2 / subpath.name))  # do not need result
    return True


class GoodreadsTestCase:
    diff: Optional[List[str]] = None

    def __init__(self, folder: str):
        self.folder_expected = RESOURCES / folder / "books"
        self.books_folder = RESOURCES / folder / "existed"
        self.csv = RESOURCES / folder / "goodreads_library_export.csv"

    def check(self, folder: str) -> bool:
        return paths_content_is_same(self.folder_expected, Path(folder))


@pytest.fixture(scope="function", params=["create", "update"])
def test_case(request) -> GoodreadsTestCase:
    return GoodreadsTestCase(request.param)
