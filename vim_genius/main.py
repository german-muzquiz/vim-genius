"""
Main entry point for the vim-genius CLI tool.
"""

import asyncio
import logging
import os
import sys

from pydantic_ai import Agent
from pydantic_ai.settings import ModelSettings

from .config import create_model, load_config, validate_config
from .context import inject_context
from .prompts import SYSTEM_PROMPT
from .schemas import Deps, LineBuffer
from .utils import print_usage, read_prompt_file

# Set up logging configuration
logging.basicConfig(
    filename="vim_genius.log",
    filemode="w",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


async def main() -> None:
    """Main entry point of the program."""
    prompt = read_prompt_file()
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

    try:
        agent = Agent(
            create_model(model_api_family, model_name, model_api_key),
            system_prompt=SYSTEM_PROMPT,
            deps_type=Deps,
            result_type=str,
            retries=2,
        )

        print("-" * 80)
        print(f"Thinking with: {model_name}...")
        print("-" * 80)

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
            print_usage_summary(usage)
    except Exception as e:
        # Handle any exceptions that occur during LLM execution
        print(f"\n\n❌ Error: {str(e)}")
        logging.error(f"LLM execution error: {str(e)}", exc_info=True)


def print_usage_summary(usage):
    """Print a summary of token usage."""
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
