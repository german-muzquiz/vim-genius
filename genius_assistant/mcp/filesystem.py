"""
Interceptor for the filesystem MCP that enhances filesystem operations.
"""

from typing import Any, Sequence, override

from pydantic_ai import RunContext
from pydantic_ai.mcp import MCPServerStdio
from pydantic_ai.messages import BinaryContent
from pydantic_ai.models.test import TestModel
from pydantic_ai.usage import Usage

from genius_assistant.schemas import Deps
from genius_assistant.tools.backup_file import backup_file

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


class GeniusFilesystemMCP(MCPServerStdio):
    ctx: RunContext[Deps]

    def __init__(self, *args, **kwargs):
        deps = kwargs.pop("deps", None)
        self.ctx = RunContext(deps=deps, model=TestModel(), usage=Usage(), prompt="")
        super().__init__(*args, **kwargs)

    @override
    async def call_tool(
        self, tool_name: str, arguments: dict[str, Any]
    ) -> str | BinaryContent | dict[str, Any] | list[Any] | Sequence[str | BinaryContent | dict[str, Any] | list[Any]]:
        # Backup original files before write, edit, or move operations
        if tool_name in ("write_file", "edit_file", "move_file"):
            filename: str = str(arguments.get("path") or arguments.get("source", ""))
            if filename:
                backup_file(self.ctx, filename=filename)

        # Call the actual tool
        result = await super().call_tool(tool_name, arguments)

        # Remove excluded directories from directory_tree calls to not use all tokens
        # listing library or dependencies files
        filtered_result: list = []
        if tool_name == "directory_tree" and isinstance(result, list):
            filtered_result = self._remove_excluded_dirs(result)
        else:
            filtered_result = result  # type: ignore

        return filtered_result

    def _remove_excluded_dirs(self, entries: list) -> list:
        result = []
        for entry in entries:
            if entry.get("type", "file") == "directory":
                if entry.get("name") in _EXCLUDE_DIRS:
                    continue
                if "children" in entry:
                    entry["children"] = self._remove_excluded_dirs(entry["children"])
                result.append(entry)
            else:
                result.append(entry)
        return result
