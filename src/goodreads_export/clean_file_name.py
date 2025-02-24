"""Make file name safe for cloud disks."""

from typing import Optional

FILE_NAME_REPLACE_MAP = {
    "%": " percent",
    ":": "",
    "/": "_",
    ",": "",
    "\\": "_",
    "[": "(",
    "]": ")",
    "<": "(",
    ">": ")",
    "*": "x",
    "?": "",
    '"': "'",
    "|": "_",
    "#": "@",
}


def clean_file_name(
    file_name: str,
    replace_map: Optional[dict[str, str]] = None,
) -> str:
    """Replace chars unsafe for file name in MS OneDrive etc."""
    if replace_map is None:
        replace_map = FILE_NAME_REPLACE_MAP
    return "".join(replace_map.get(ch, ch) for ch in file_name)
