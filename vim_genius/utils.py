"""
Utility functions for vim-genius.
"""

import os


def print_usage() -> None:
    """Print usage instructions for the CLI."""
    usage = "Usage: python -m vim_genius\n  The prompt should be provided in the file /prompt/prompt.txt\n"
    print(usage)


def read_prompt_file() -> str:
    """
    Read prompt from the mounted file.

    Returns:
        Prompt content or None if file doesn't exist
    """
    prompt_file = "/root/.genius/current_chat.genius"
    if os.path.exists(prompt_file):
        with open(prompt_file, "r", encoding="utf-8") as f:
            contents = f.read()
            # Remove header (first 13 lines)
            contents = "\n".join(contents.split("\n")[13:])
            return contents
    return ""


def print_usage_summary(usage) -> None:
    """
    Print a summary of token usage.

    Args:
        usage: The usage object from the LLM response
    """
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
