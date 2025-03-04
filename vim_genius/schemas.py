"""
Data schemas for vim-genius.
"""

from typing import Optional

from pydantic import BaseModel


class Deps(BaseModel):
    """Dependencies injected into tools."""

    brave_api_key: Optional[str] = None


class WebSearchResult(BaseModel):
    """Result from a web search."""

    title: str
    url: str
    snippet: str


class LineBuffer:
    """
    A buffer that accumulates text and outputs complete lines.
    """

    def __init__(self):
        self.buffer = ""

    def add_text(self, text: str) -> list[str]:
        """
        Add text to the buffer and return any complete lines.

        Args:
            text: The text to add to the buffer

        Returns:
            A list of complete lines
        """
        self.buffer += text
        lines = []

        while "\n" in self.buffer:
            line, self.buffer = self.buffer.split("\n", 1)
            lines.append(line)

        return lines

    def get_remaining(self) -> str:
        """
        Get any remaining text in the buffer.

        Returns:
            The remaining text
        """
        return self.buffer
