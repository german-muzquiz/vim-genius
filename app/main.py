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
from crawl4ai import AsyncWebCrawler, BrowserConfig
from dotenv import load_dotenv
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

<output_format_instructions>
- Output code without descriptions, unless it is important.
- Minimize prose, output directly code blocks preceded by the file name if applicable.
- Limit lines to 100 characters, except for code blocks.
- Make it easy to copy and paste.

- For each code piece in the output use the appropriate code block syntax. For example for python code blocks use this syntax:
```python
def sum(a: int, b: int) -> int:
    pass
```

- For each file of the code that needs to be modified, produce a separate code block showing the added, deleted and changed lines in diff unified format.
Example:

`pyproject.toml`
```diff
--- a/pyproject.toml
+++ b/pyproject.toml
@@ -1,7 +1,6 @@
[project]
-dependencies = [
-]
+dependencies = [
+    "smolagents>=0.0.1",
+]
@@ -9,3 +8,6 @@
[tool.poetry.scripts]
-smolagents = "smolagents.cli:main"
+smolagents = "smolagents.cli:main"
+
+[tool.poetry.dependencies]
+smolagents = "^0.0.1"
```

- For each new file produce a separate code block.
Example:
`new_file.py`
```python
class A:
    pass
```

- Every code block should be surrounded by empty blank lines to improve readablity.
</output_format_instructions>

- Consider other possibilities to achieve the result, do not be limited by the prompt.
- All functions should be smaller than 30 lines, refactor to helper functions when appropriate.
- Add comments to the code to make it easy to understand.
- For python code always use docstrings to document public functions, classes and modules.
"""  # noqa: E501


class Deps(BaseModel):
    """Dependencies injected into tools."""

    brave_api_key: Optional[str]


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


def parse_args() -> Optional[str]:
    """
    Parse command line arguments.

    Returns:
        Prompt
    """
    args = sys.argv[1:]
    prompt: Optional[str] = None

    if "--prompt" in args:
        idx = args.index("--prompt")
        if idx + 1 < len(args):
            prompt = args[idx + 1]

    return prompt


def validate_config() -> None:
    """Validate configuration settings."""
    api_family = os.getenv("API_FAMILY", "")
    model_name = os.getenv("MODEL_NAME", "")
    model_api_key = os.getenv("MODEL_API_KEY", "")

    if not api_family or not model_name:
        raise ValueError("API_FAMILY and MODEL_NAME must be set in ~/.vim_genius")

    if api_family != "bedrock" and not model_api_key:
        raise ValueError("MODEL_API_KEY must be set in ~/.vim_genius for non-bedrock APIs")


def create_model(api_family: str, model_name: str, api_key: str) -> Model:
    match api_family:
        case "openai":
            return OpenAIModel(model_name, api_key=api_key)
        case "anthropic":
            return AnthropicModel(model_name, api_key=api_key)
        case "bedrock":
            return BedrockModel(model_name)
        case "openrouter":
            return OpenAIModel(
                model_name,
                api_key=api_key,
                base_url="https://openrouter.ai/api/v1",
            )
        case _:
            raise ValueError(f"Unknown model api family: {api_family}")


def load_config() -> None:
    """
    Load configuration from ~/.vim_genius file into environment variables.
    """
    # Config file is in user home directory
    config_file = os.path.expanduser("~/.vim_genius")
    if not os.path.exists(config_file):
        raise FileNotFoundError(f"Configuration file not found: {config_file}")

    # Load environment variables from config file
    load_dotenv(config_file)


async def load_url_content(url: str) -> str:
    browser_config = BrowserConfig(verbose=False)
    async with AsyncWebCrawler(config=browser_config) as crawler:
        print(f"Loading URL: {url}")
        result = await crawler.arun(url)
        return result.markdown


async def inject_entry(entry: str) -> dict[str, str]:
    result: dict[str, str] = {}
    entry = entry.strip()

    # Url loading
    if entry.startswith("http"):
        content = await load_url_content(entry)
        result[entry] = content
        return result

    # File loading
    if not os.path.isabs(entry):
        entry = os.path.join("/context", entry)
    if os.path.isdir(entry):
        # For reproducible order, sort the file list.
        for dir_entry in sorted(os.listdir(entry)):
            result.update(await inject_entry(os.path.join(entry, dir_entry)))
    elif os.path.isfile(entry):
        content = load_file_content(entry)
        result[entry] = content
    else:
        result[entry] = "Could not find file or folder"
    return result


async def inject_context(user_input: str) -> str:
    # This regex finds tokens such as "@filename" or "@folder/"
    tokens = re.findall(r"@(\S+)", user_input)
    injection_chunks: list[str] = []
    for token in tokens:
        context = await inject_entry(token)
        for file_path, content in context.items():
            if file_path.startswith("http"):
                file_extension = "md"
            else:
                file_extension = os.path.splitext(file_path)[1][1:] or os.path.basename(file_path)
            injection_chunks.append(f"`{file_path}` contents:\n```{file_extension}\n{content}\n```")

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


async def main() -> None:
    """Main entry point of the program."""
    prompt = parse_args()
    load_config()

    if not prompt:
        logging.error("Error: --prompt is a mandatory argument")
        print_usage()
        sys.exit(1)

    user_prompt = await inject_context(prompt)
    validate_config()
    model_api_family = os.getenv("API_FAMILY", "")
    model_name = os.getenv("MODEL_NAME", "")
    model_api_key = os.getenv("MODEL_API_KEY", "")

    # print("User prompt:")
    # print(user_prompt)

    agent = Agent(
        create_model(model_api_family, model_name, model_api_key),
        system_prompt=_SYSTEM_PROMPT,
        deps_type=Deps,
        result_type=str,
        retries=2,
    )

    print(f"==> Thinking with model: {model_name}...\n")

    # Create a line buffer to accumulate text
    line_buffer = LineBuffer()

    async with agent.run_stream(
        user_prompt,
        deps=Deps(brave_api_key=os.getenv("BRAVE_API_KEY")),
        model_settings=ModelSettings(max_tokens=8192, temperature=0.0),
    ) as result:
        async for message in result.stream_text(delta=True):
            # Add the message to the buffer and get any complete lines
            complete_lines = line_buffer.add_text(message)

            # Output each complete line
            for line in complete_lines:
                print(line)

        # Output any remaining text in the buffer
        remaining = line_buffer.get_remaining()
        if remaining:
            print(remaining)

        # Print token usage information at the end of the output
        usage = result.usage()
        print("\n" + "-" * 80)
        print("Token Usage Summary:")
        print(f"  Requests: {usage.requests}")
        if usage.request_tokens is not None:
            print(f"  Request tokens: {usage.request_tokens}")
        if usage.response_tokens is not None:
            print(f"  Response tokens: {usage.response_tokens}")
        if usage.total_tokens is not None:
            print(f"  Total tokens: {usage.total_tokens}")
        print("-" * 80)


if __name__ == "__main__":
    asyncio.run(main())
