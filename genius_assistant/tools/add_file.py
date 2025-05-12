"""
Tool that adds a new file to the workspace.
"""

import os

from pydantic_ai import ModelRetry, RunContext

from genius_assistant.schemas import Deps


def add_file(ctx: RunContext[Deps], filename: str, content: str) -> bool:
    """
    Creates a new file in the workspace.

    Args:
        ctx: The context object containing the dependencies.
        filename: The name of the file to create relative to the workspace root.
        content: The content of the file to create.

    Returns:
        True if the file was created successfully, False otherwise.
    """
    print(f"=> Creating file: {filename}")

    if os.path.isabs(filename) and not filename.startswith(ctx.deps.workspace_home):
        raise ModelRetry(f"File {filename} is not in the workspace")
    elif os.path.isabs(filename):
        file_path = filename
    else:
        file_path = os.path.join(ctx.deps.workspace_home, filename)

    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    # Create a new empty file in the backup folder for viewing diffs
    backup_root = os.path.expanduser("~/.genius/backup")
    abs_file = file_path
    # Compute relative path to workspace
    rel_path = os.path.relpath(abs_file, ctx.deps.workspace_home)
    backup_path = os.path.join(backup_root, rel_path)
    if not os.path.exists(backup_path):
        os.makedirs(os.path.dirname(backup_path), exist_ok=True)
        with open(backup_path, "w", encoding="utf-8") as f:
            f.write("")

    return True
