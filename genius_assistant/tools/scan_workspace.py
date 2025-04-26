"""
Tool that lists the files in the current workspace.
"""

import os

from pydantic_ai import RunContext

from ..schemas import Deps

_EXCLUDE_DIRS = [
    ".git",
    ".venv",
    ".pytest_cache",
    ".mypy_cache",
    ".vscode",
    "node_modules",
    "build",
    "dist",
    "__pycache__",
    ".mypy_cache",
    ".ruff_cache",
]
_MAX_COUNT = 100


def scan_workspace(ctx: RunContext[Deps]) -> list[str]:
    """
    Lists the files in the current workspace.

    Args:
        ctx: The context object containing the dependencies.

    Returns:
        A list of file paths.
    """
    workspace_home = ctx.deps.workspace_home
    print(f"=> Listing files in current workspace ({workspace_home})")
    return get_workspace_files(workspace_home)


def get_workspace_files(workspace_home: str) -> list[str]:
    file_paths: list[str] = []
    for root, dirs, files in os.walk(workspace_home):
        dirs[:] = [d for d in dirs if d not in _EXCLUDE_DIRS]
        for file in files:
            file_path = os.path.join(root, file)
            if len(file_paths) >= _MAX_COUNT:
                file_paths.append(f"Reached maximum number of files to list ({_MAX_COUNT}), aborting")
                return file_paths
            file_paths.append(file_path)
        for dir in dirs:
            dir_path = os.path.join(root, dir)
            file_paths.append(dir_path)
    return file_paths
