"""
Tool that performs a web search using the Brave API.
"""

import os
from typing import Union

from pydantic_ai import RunContext
from pydantic_ai.tools import ToolDefinition

from genius_assistant.schemas import Deps, WebSearchResult


async def prepare_web_search(ctx: RunContext[Deps], tool_def: ToolDefinition) -> Union[ToolDefinition | None]:
    if not os.getenv("BRAVE_API_KEY"):
        return None
    return tool_def


def web_search(ctx: RunContext[Deps], query: str) -> list[WebSearchResult]:
    """
    Perform a web search using the Brave API.

    Args:
        ctx: The context object containing the dependencies.
        query: The search query to perform.

    Returns:
        A list of WebSearchResult objects.
    """
    print(f"\n<web_search>Searching the web for: {query}</web_search>\n")
    return []
    # assert ctx.deps.brave_api_key
    # with httpx.Client() as client:
    #     response = client.get(
    #         "https://api.search.brave.com/res/v1/web/search",
    #         params={"q": query},
    #         headers={"X-Subscription-Token": ctx.deps.brave_api_key},
    #     )
    #     results = response.json()
    #     return [
    #         WebSearchResult(title=r["title"], url=r["url"], snippet=r["description"])
    #         for r in results.get("web", {}).get("results", [])
    #     ]
