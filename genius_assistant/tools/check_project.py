"""
Tool that lints a file to scan for errors.
"""

import os
import subprocess
from typing import Union

from pydantic_ai import ModelRetry, RunContext
from pydantic_ai.tools import ToolDefinition

from ..schemas import Deps
from ..utils import load_tasks_config


async def prepare_check_project(ctx: RunContext[Deps], tool_def: ToolDefinition) -> Union[ToolDefinition | None]:
    if not os.path.exists(os.path.join(ctx.deps.workspace_home, ".tasks")):
        return None
    tasks_path = os.path.join(ctx.deps.workspace_home, ".tasks")
    configs = load_tasks_config(tasks_path)
    section = "check-project"
    if section not in configs:
        return None

    conf = configs[section]
    if "command" not in conf:
        return None

    return tool_def


def check_project(ctx: RunContext[Deps]) -> str:
    """
    Verifies the current project by linting and compiling it.
    Depends on the file `.tasks` in the root of the project to define the command to run.

    Args:
        ctx: The context object containing the dependencies.

    Returns:
        A string indicating the result of the check.
    """
    print("=> Checking project")

    if not os.path.exists(os.path.join(ctx.deps.workspace_home, ".tasks")):
        raise ModelRetry(f"File .tasks does not exist in {ctx.deps.workspace_home}")

    try:
        # Load tasks configuration and extract the check-project settings
        tasks_path = os.path.join(ctx.deps.workspace_home, ".tasks")
        configs = load_tasks_config(tasks_path)
        section = "check-project"
        if section not in configs:
            return f"Section '{section}' not found in {tasks_path}"

        conf = configs[section]
        if "command" not in conf:
            return f"Command not found in section '{section}' in {tasks_path}"

        command = conf.get("command", "")

        parts = command.split()
        # Remove VIRTUAL_ENV from environment variables for subprocess
        env = os.environ.copy()
        env.pop("VIRTUAL_ENV", None)
        result = subprocess.run(
            parts,
            check=True,
            capture_output=True,
            text=True,
            cwd=ctx.deps.workspace_home,
            env=env,
        )
        return result.stdout or ""
    except subprocess.CalledProcessError as e:
        print(e.stderr)
        return e.stderr
    except Exception as e:
        print(e)
        raise ModelRetry(f"Error executing .tasks command: {e}")
