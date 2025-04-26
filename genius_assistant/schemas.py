"""
Data schemas for vim-genius.
"""

from typing import Optional

from pydantic import BaseModel, Field


class Deps(BaseModel):
    """Dependencies injected into tools."""

    brave_api_key: Optional[str] = None
    workspace_home: str
    modified_files: list[str] = Field(default=[], description="List of modified files during the agent run")


class WebSearchResult(BaseModel):
    """Result from a web search."""

    title: str
    url: str
    snippet: str
