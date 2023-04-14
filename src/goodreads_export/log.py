"""Logger."""
import os
from textwrap import shorten
from typing import Dict, Optional

from tqdm import tqdm


class Log:
    """Logger.

    In non-verbose mode show progress bar instead of log.
    In verbose mode ignore all progress bars' specific commands.
    """

    progress_bar: Dict[str, Dict[str, tqdm]] = {}
    position = 0

    def __init__(self, verbose: bool = False) -> None:
        """Initialize logger."""
        self._verbose = verbose

    @staticmethod
    def get_terminal_width() -> int:
        """Get terminal size."""
        try:
            return os.get_terminal_size().columns
        except OSError:
            return 80  # something capturing stdout, most likely Click test runner

    def start(self, message: str) -> None:
        """Start message."""
        print(f"{message}...", **({} if self._verbose else {"end": ""}))  # type: ignore

    def open_progress(
        self, title: str, unit: str, num: Optional[int] = None, bar_format: Optional[str] = None
    ) -> None:
        """Open progress bar."""
        if not self._verbose:
            self.progress_bar[title] = {
                "title": tqdm(bar_format="{desc}", leave=False, position=self.position + 1),
                "bar": tqdm(
                    total=num, desc=title, unit=f" {unit}", leave=False, position=self.position + 2
                ),
            }
            if bar_format:
                self.progress_bar[title]["bar"].bar_format = bar_format
            self.position += 2

    def progress_description(self, title: str, message: str) -> None:
        """Update progress bar description.

        Or log the message if we are in verbose mode.
        """
        if not self._verbose:
            self.progress_bar[title]["title"].set_description_str(
                shorten(message, self.get_terminal_width())
            )
        else:
            print(f"{title}: {message}")

    def progress(self, title: str) -> None:
        """Update progress bar."""
        if not self._verbose:
            self.progress_bar[title]["bar"].update()

    def close_progress(self) -> None:
        """Close progress bars."""
        if not self._verbose:
            for progress_bar in self.progress_bar.values():
                progress_bar["bar"].close()
                progress_bar["title"].close()
            self.progress_bar = {}
            self.position = 0

    def progress_refresh(self) -> None:
        """Refresh progress bars."""
        if not self._verbose:
            for progress_bar in self.progress_bar.values():
                progress_bar["bar"].refresh()
                progress_bar["title"].refresh()

    def debug(self, message: str) -> None:
        """Print debug message.

        Do nothing in non-verbose mode.
        """
        if self._verbose:
            print(message)

    def info(self, message: str) -> None:
        """Print info messages."""
        print(message)

    def error(self, message: str) -> None:
        """Print error messages."""
        print(message)
