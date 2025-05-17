"""
Tool that registers a new cli command that the assistant llm can execute.
"""

import os

from pydantic_ai import ModelRetry, RunContext

from genius_assistant.schemas import Deps
from genius_assistant.utils import load_tasks_config


def register_cli_command(ctx: RunContext[Deps], name: str, cmd: str) -> None:
    """
    Registers a new cli command that the assistant llm can execute.

    Args:
        ctx: The context object containing the dependencies.
        name: The name of the command.
        cmd: The command to register.

    Returns:
        None
    """
    try:
        # Load or create tasks configuration file
        tasks_path = os.path.join(ctx.deps.workspace_home, ".tasks")
        if not os.path.exists(tasks_path):
            with open(tasks_path, "w", encoding="utf-8") as f:
                f.write("")
        configs = load_tasks_config(tasks_path)
        if name not in configs:
            # Create a new section for the command
            configs[name] = {
                "command": cmd,
                "cwd": "$(VIM_ROOT)",
                "output": "terminal",
                "save": "0",
                "focus": "0",
                "pos": "bottom",
                "close": "0",
            }
        else:
            # Update the command in the existing section
            configs[name]["command"] = cmd

        # Save the tasks configuration file
        with open(tasks_path, "w", encoding="utf-8") as f:
            for section, conf in configs.items():
                f.write(f"[{section}]\n")
                for key, value in conf.items():
                    f.write(f"{key} = {value}\n")
                f.write("\n")
    except Exception as e:
        raise ModelRetry(f"Failed to register cli command: {e}")
