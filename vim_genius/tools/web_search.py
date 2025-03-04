"""
Tool that performs a web search using the Brave API.
"""

import httpx
from pydantic_ai import RunContext

from ..schemas import Deps, WebSearchResult


def web_search(ctx: RunContext[Deps], query: str) -> list[WebSearchResult]:
    """
    Perform a web search using the Brave API.

    Args:
        ctx: The context object containing the dependencies.
        query: The search query to perform.

    Returns:
        A list of WebSearchResult objects.
    """
    assert ctx.deps.brave_api_key
    with httpx.Client() as client:
        response = client.get(
            "https://api.search.brave.com/res/v1/web/search",
            params={"q": query},
            headers={"X-Subscription-Token": ctx.deps.brave_api_key},
        )
        results = response.json()
        return [
            WebSearchResult(title=r["title"], url=r["url"], snippet=r["description"])
            for r in results.get("web", {}).get("results", [])
        ]
