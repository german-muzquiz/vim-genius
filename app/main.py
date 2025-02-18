"""
Main entry point for the vim-genius CLI tool.
"""

import asyncio
import logging
import os
import re
import sys
from typing import Optional

import httpx
from pydantic import BaseModel
from pydantic_ai import Agent, RunContext
from pydantic_ai.models import Model
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.settings import ModelSettings
from pydantic_ai_bedrock.bedrock import (
    BedrockModel,
)  # Replace with `pydantic_ai.bedrock import BedrockModel` when pydantic_ai support bedrock

# Set up logging configuration
logging.basicConfig(
    filename="vim_genius.log",
    filemode="w",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

_SYSTEM_PROMPT = """
You are an expert coding assistant.

Instructions for your output format:
- Output code without descriptions, unless it is important.
- Minimize prose and empty lines.
- Make it easy to copy and paste.
- Consider other possibilities to achieve the result, do not be limited by the prompt.
- For each code piece in the output use the appropriate code block syntax. For example for python code blocks use this syntax:
```python
def sum(a: int, b: int) -> int:
    pass
```
- For each file of the code that needs to be modified, produce a separate code block showing the added, deleted and changed lines in diff format.
Example:
diff --git a/pyproject.toml b/pyproject.toml
```
--- a/pyproject.toml
@@ [project]
-dependencies = [
-]
+dependencies = [
    "smolagents>=0.0.1",
+]
```
- For each new file produce a separate code block.
Example:
```python
class A:
    pass
```
- All functions should be smaller than 30 lines, refactor to helper functions when appropriate.
- Add comments to the code to make it easy to understand.
"""  # noqa: E501


class Deps(BaseModel):
    """Dependencies injected into tools."""

    brave_api_key: str


class WebSearchResult(BaseModel):
    title: str
    url: str
    snippet: str


def print_usage() -> None:
    """Print usage instructions for the CLI."""
    usage = (
        "Usage: python -m vim_genius --prompt <prompt> --model <model-name> [--files <file1,file2,...>]\n"
        "  --prompt: The prompt to send to the model (mandatory).\n"
        "  --model: The model name to use for generating the suggestion (mandatory).\n"
        "  --files: Comma-separated list of files to include in the context (optional).\n"
    )
    print(usage)


def load_file_content(file: str) -> str:
    file_path = file.strip()

    if not os.path.isabs(file_path):
        file_path = os.path.join("/context", file_path)

    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            content = f"Error reading file {file_path}: {str(e)}"
    else:
        content = f"File not found: {file_path}"

    return content


def parse_args() -> tuple[Optional[str], Optional[str]]:
    """
    Parse command line arguments.

    Returns:
        Tuple of (prompt, model_name)
    """
    args = sys.argv[1:]
    prompt: Optional[str] = None
    model_name: Optional[str] = None

    if "--prompt" in args:
        idx = args.index("--prompt")
        if idx + 1 < len(args):
            prompt = args[idx + 1]

    if "--model" in args:
        idx = args.index("--model")
        if idx + 1 < len(args):
            model_name = args[idx + 1]

    return prompt, model_name


def create_model(model_name: str) -> Model:
    model_family = model_name.split(":", 1)[0]
    match model_family:
        case "openai":
            return OpenAIModel(model_name.split(":", 1)[1])
        case "anthropic":
            return AnthropicModel(model_name.split(":", 1)[1])
        case "bedrock":
            return BedrockModel(model_name.split(":", 1)[1])
        case _:
            raise ValueError(f"Unknown model family: {model_family}")


def inject_entry(entry: str) -> dict[str, str]:
    result: dict[str, str] = {}
    if not os.path.isabs(entry):
        entry = os.path.join("/context", entry)
    if os.path.isdir(entry):
        # For reproducible order, sort the file list.
        for dir_entry in sorted(os.listdir(entry)):
            result.update(inject_entry(os.path.join(entry, dir_entry)))
    elif os.path.isfile(entry):
        content = load_file_content(entry)
        result[entry] = content
    else:
        result[entry] = "Could not find file or folder"
    return result


def inject_context(user_input: str) -> str:
    # This regex finds tokens such as "@filename" or "@folder/"
    tokens = re.findall(r"@(\S+)", user_input)
    injection_chunks: list[str] = []
    for token in tokens:
        for file_path, content in inject_entry(token).items():
            file_extension = os.path.splitext(file_path)[1][1:] or os.path.basename(file_path)
            injection_chunks.append(f"{file_path}\n```{file_extension}\n{content}\n```")

    # Remove all @tokens from the original user prompt.
    adjusted_prompt = re.sub(r"@\S+", "", user_input)

    # Append a newline and then the injected content.
    if injection_chunks:
        adjusted_prompt += "\n" + "\n".join(injection_chunks)

    return adjusted_prompt


def web_search(ctx: RunContext[Deps], query: str) -> list[WebSearchResult]:
    """
    Perform a web search using the Brave API.

    Args:
        ctx: The context object containing the dependencies.
        query: The search query to perform.

    Returns:
        A list of WebSearchResult objects.
    """
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


async def main() -> None:
    """Main entry point of the program."""
    prompt, model_name = parse_args()

    if not prompt or not model_name:
        logging.error("Error: --prompt and --model are mandatory arguments")
        print_usage()
        sys.exit(1)

    user_prompt = inject_context(prompt)

    # print("User prompt:")
    # print(user_prompt)

    agent = Agent(
        create_model(model_name),
        system_prompt=_SYSTEM_PROMPT,
        deps_type=Deps,
        # tools=[Tool(web_search, takes_ctx=True)],  Commented until https://github.com/pydantic/pydantic-ai/pull/833 is merged
        result_type=str,
        retries=2,
    )

    async with agent.run_stream(
        user_prompt,
        deps=Deps(brave_api_key=os.getenv("BRAVE_API_KEY")),
        model_settings=ModelSettings(max_tokens=8192, temperature=0.0),
    ) as result:
        async for message in result.stream_text(delta=True):
            print(message, end="", flush=True)
        print("")


if __name__ == "__main__":
    asyncio.run(main())
