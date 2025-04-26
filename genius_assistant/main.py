"""
Main entry point for the vim-genius CLI tool.
"""

import asyncio
import os
import sys
import traceback

from pydantic_ai import Agent, Tool
from pydantic_ai.settings import ModelSettings

from .code_blocks import extract_code_blocks, process_code_blocks
from .config import create_model, load_config, validate_config
from .context import inject_context
from .prompts import SYSTEM_PROMPT
from .schemas import Deps
from .tools import check_project, edit_file, prepare_check_project, read_file, scan_workspace, web_search
from .utils import read_prompt_file


def print_usage_summary(usage):
    """Print a summary of token usage."""
    print("")
    print("\n" + "-" * 81)
    print("Token Usage Summary:")
    print(f"  Requests: {usage.requests}")
    if usage.request_tokens is not None:
        print(f"  Request tokens: {usage.request_tokens}")
    if usage.response_tokens is not None:
        print(f"  Response tokens: {usage.response_tokens}")
    if usage.total_tokens is not None:
        print(f"  Total tokens: {usage.total_tokens}")
    print("-" * 81)


async def main(workspace_home: str) -> None:
    """Main entry point of the program."""
    if not os.path.isdir(workspace_home):
        raise FileNotFoundError(f"Workspace {workspace_home} not found or is not a directory")

    prompt = read_prompt_file()
    load_config()

    if not prompt:
        print("No prompt given")
        sys.exit(1)

    user_prompt = await inject_context(prompt, workspace_home)
    validate_config()
    model_api_family = os.getenv("API_FAMILY", "")
    model_name = os.getenv("MODEL_NAME", "")
    model_api_key = os.getenv("MODEL_API_KEY", "")

    # print("User prompt:")
    # print("\n".join(user_prompt))  # type: ignore

    try:
        tools: list[Tool[Deps]] = [
            Tool(edit_file, takes_ctx=True),
            Tool(scan_workspace, takes_ctx=True),
            Tool(read_file, takes_ctx=True),
            Tool(check_project, prepare=prepare_check_project, takes_ctx=True),
        ]

        if os.getenv("BRAVE_API_KEY"):
            tools.append(Tool(web_search, takes_ctx=True))

        # Create the agent
        agent = Agent(
            create_model(model_api_family, model_name, model_api_key),
            system_prompt=SYSTEM_PROMPT,
            deps_type=Deps,
            result_type=str,
            retries=2,
            tools=tools,
        )

        print("")
        print("-" * 81)
        print(f"Model: {model_name}")
        print("-" * 81)

        result = await agent.run(
            user_prompt,
            deps=Deps(brave_api_key=os.getenv("BRAVE_API_KEY"), workspace_home=workspace_home),
            model_settings=ModelSettings(max_tokens=8192, temperature=0.0),
        )

        # Print the complete response
        print(result.output)

        # Extract and process code blocks
        code_blocks = extract_code_blocks(result.output)
        if code_blocks:
            process_code_blocks(code_blocks, workspace_home)
        print_usage_summary(result.usage())

        print("")
        print("-" * 81)
        print("User Turn")
        print("-" * 81)
        print("")
    except Exception as e:
        # Handle any exceptions that occur during LLM execution
        print(f"\n\n❌ Error: {str(e)}")
        traceback.print_exc()


if __name__ == "__main__":
    workspace_home = sys.argv[1]
    asyncio.run(main(workspace_home))
