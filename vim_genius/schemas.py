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
