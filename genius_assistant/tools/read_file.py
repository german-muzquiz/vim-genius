"""
Tool that reads the contents of one file.
"""

import os

from pydantic_ai import ModelRetry, RunContext

from genius_assistant.schemas import Deps


def read_file(ctx: RunContext[Deps], filename: str) -> str:
    """
    Read the contents of a file.

    Args:
        ctx: The context object containing the dependencies.
        filename: The name of the file to read.

    Returns:
        The contents of the file.
    """
    print(f"=> Reading file: {filename}")

    if os.path.isabs(filename):
        file_path = filename
    elif filename.startswith(ctx.deps.workspace_home):
        file_path = filename
    else:
        file_path = os.path.join(ctx.deps.workspace_home, filename)

    if not os.path.exists(file_path):
        msg = f"File {file_path} does not exist"
        print(msg)
        raise ModelRetry(msg)

    with open(file_path, "r") as f:
        return f.read()
