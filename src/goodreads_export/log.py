"""Logger."""
from typing import Dict, Optional

from tqdm import tqdm


class Log:
    """Logger or progress bar."""

    progress_bar: Dict[str, Dict[str, tqdm]] = {}
    position = 0

    def __init__(self, verbose: bool = False) -> None:
        """Initialize logger."""
        self.verbose = verbose

    def start(self, message: str) -> None:
        """Start message."""
        print(f"{message}...", **({} if self.verbose else {"end": ""}))  # type: ignore

    def open_progress(self, title: str, unit: str, num: Optional[int] = None) -> None:
        """Open progress bar."""
        if not self.verbose:
            self.progress_bar[title] = {
                "title": tqdm(bar_format="{desc}", leave=False, position=self.position + 1),
                "bar": tqdm(
                    total=num, desc=title, unit=f" {unit}", leave=False, position=self.position + 2
                ),
            }
            self.position += 2

    def progress_description(self, title: str, message: str) -> None:
        """Update progress bar description."""
        if not self.verbose:
            self.progress_bar[title]["title"].set_description_str(message)

    def progress(self, title: str) -> None:
        """Update progress bar."""
        if not self.verbose:
            self.progress_bar[title]["bar"].update()

    def close_progress(self, title: str) -> None:
        """Close progress bar."""
        if not self.verbose:
            self.progress_bar[title]["bar"].close()
            self.progress_bar[title]["title"].close()
            del self.progress_bar[title]
            self.position -= 2

    def debug(self, message: str) -> None:
        """Do not print debug messages in non-verbose mode."""
        if self.verbose:
            print(message)
