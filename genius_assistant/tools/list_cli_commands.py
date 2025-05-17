"""
Tool that lists all the available commands that the assistant llm can execute.
"""

import os

from pydantic_ai import ModelRetry, RunContext

from genius_assistant.schemas import Deps
from genius_assistant.utils import load_tasks_config


def list_cli_commands_raw(deps: Deps) -> dict[str, str]:
    try:
        # Load the tasks configuration file
        tasks_path = os.path.join(deps.workspace_home, ".tasks")
        if not os.path.exists(tasks_path):
            return {}

        configs = load_tasks_config(tasks_path)

        return {name: conf.get("command", "") for name, conf in configs.items()}
    except Exception as e:
        raise ModelRetry(f"Failed to list commands: {e}")


def list_cli_commands(ctx: RunContext[Deps]) -> dict[str, str]:
    """
    Lists all the available commands that the assistant llm can execute.

    Args:
        ctx: The context object containing the dependencies.

    Returns:
        A dictionary of command names and the actual command.
    """
    return list_cli_commands_raw(ctx.deps)
