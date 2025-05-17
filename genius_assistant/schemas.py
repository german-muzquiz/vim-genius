"""
Data schemas for vim-genius.
"""


from pydantic import BaseModel, Field


class Deps(BaseModel):
    """Dependencies injected into tools."""

    workspace_home: str
    modified_files: list[str] = Field(default=[], description="List of modified files during the agent run")
    tool_invocations: int = 0


class WebSearchResult(BaseModel):
    """Result from a web search."""

    title: str
    url: str
    snippet: str
