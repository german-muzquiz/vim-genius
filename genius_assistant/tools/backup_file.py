"""
Tool that takes a backup of a file in the workspace.
"""

import os
import shutil

from pydantic_ai import ModelRetry, RunContext

from genius_assistant.schemas import Deps


def backup_file(ctx: RunContext[Deps], filename: str) -> None:
    """
    Takes a backup of an existing or new file in the workspace.

    Args:
        ctx: The context object containing the dependencies.
        filename: The name of the file to backup.

    Returns:
        None
    """
    if os.path.isabs(filename) and not filename.startswith(ctx.deps.workspace_home):
        raise ModelRetry(f"File {filename} is not in the workspace")

    if not os.path.isabs(filename):
        filename = os.path.join(ctx.deps.workspace_home, filename)

    # Backup original file to ~/.genius/backup preserving structure, skip if already backed up
    backup_root = os.path.expanduser("~/.genius/backup")
    abs_file = filename
    # Compute relative path to workspace
    rel_path = os.path.relpath(abs_file, ctx.deps.workspace_home)
    backup_path = os.path.join(backup_root, rel_path)
    if not os.path.exists(backup_path):
        os.makedirs(os.path.dirname(backup_path), exist_ok=True)
        if os.path.exists(abs_file):
            shutil.copy2(abs_file, backup_path)
        else:
            open(backup_path, "w").close()

    ctx.deps.modified_files.append(filename)
