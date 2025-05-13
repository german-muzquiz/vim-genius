"""
Tool that lists the files in the current workspace.
"""

import os

from pydantic_ai import RunContext

from genius_assistant.schemas import Deps

_EXCLUDE_DIRS = [
    ".git",
    ".venv",
    ".env",
    ".pytest_cache",
    ".idea",
    ".mypy_cache",
    ".vscode",
    "node_modules",
    "build",
    "dist",
    "target",
    "__pycache__",
    ".mypy_cache",
    ".ruff_cache",
    ".terraform",
]
_MAX_COUNT = 400


def scan_workspace(ctx: RunContext[Deps]) -> list[str]:
    """
    Lists the files in the current workspace.

    Args:
        ctx: The context object containing the dependencies.

    Returns:
        A list of file paths.
    """
    workspace_home = ctx.deps.workspace_home
    print(f"=> Listing files in current workspace ({workspace_home})... ", end="")
    files = get_workspace_files(workspace_home)
    print(f"found {len(files)} files")
    return files


def get_workspace_files(workspace_home: str) -> list[str]:
    to_exclude = _get_exclude_list(workspace_home)

    file_paths: list[str] = []
    for root, dirs, files in os.walk(workspace_home):
        # Prune directories by base name and gitignore patterns
        pruned_dirs: list[str] = []
        for d in dirs:
            if d in to_exclude:
                continue
            rel_dir = os.path.normpath(os.path.relpath(os.path.join(root, d), workspace_home))
            if any(rel_dir == pat or rel_dir.startswith(pat + os.sep) for pat in to_exclude):
                continue
            pruned_dirs.append(d)
        dirs[:] = pruned_dirs

        # Add files
        for f in files:
            file_path = os.path.join(root, f)
            if len(file_paths) >= _MAX_COUNT:
                file_paths.append(f"Reached maximum number of files to list ({_MAX_COUNT}), aborting")
                return file_paths
            file_paths.append(file_path)

        # Optionally include directory paths
        for d in dirs:
            dir_path = os.path.join(root, d)
            file_paths.append(dir_path)

    return file_paths


def _get_exclude_list(workspace_home: str) -> set[str]:
    # Build exclude lists: base names and relative path patterns
    pattern_excludes: list[str] = []
    gitignore_file = os.path.join(workspace_home, ".gitignore")
    if os.path.exists(gitignore_file):
        with open(gitignore_file, "r") as g:
            for line in g:
                entry = line.strip()
                # only directory entries (ending with '/')
                if entry and entry.endswith("/") and not entry.startswith("#"):
                    # normalize and strip trailing slash
                    pattern_excludes.append(os.path.normpath(entry.rstrip("/")))

    return set(_EXCLUDE_DIRS + pattern_excludes)


if __name__ == "__main__":
    files = get_workspace_files("/Users/german/code/ai-omni-agent")
    print(f"Found {len(files)} files")
    for f in files:
        print(f"- {f}")
