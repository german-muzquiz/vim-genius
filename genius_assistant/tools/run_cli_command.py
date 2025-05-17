"""
Tool that runs a cli command previously registered and available in the .tasks file.
"""

import os
import subprocess

from pydantic_ai import ModelRetry, RunContext

from genius_assistant.schemas import Deps
from genius_assistant.utils import load_tasks_config


def run_cli_command(ctx: RunContext[Deps], command_name: str) -> str:
    """
    Runs a cli command previously registered and available in the .tasks file.

    Args:
        ctx: The context object containing the dependencies.
        command_name: The name of the command to run.

    Returns:
        A string indicating the result of the command.
    """
    if not os.path.exists(os.path.join(ctx.deps.workspace_home, ".tasks")):
        raise ModelRetry(f"File .tasks does not exist in {ctx.deps.workspace_home}")

    try:
        # Load tasks configuration and extract the command settings
        tasks_path = os.path.join(ctx.deps.workspace_home, ".tasks")
        configs = load_tasks_config(tasks_path)
        section = command_name
        if section not in configs:
            return f"Section '{section}' not found in {tasks_path}"

        conf = configs[section]
        if "command" not in conf:
            return f"Command not found in section '{section}' in {tasks_path}"

        command = conf.get("command", "")
        print(f"({command})... ", end="")

        result = subprocess.run(
            ["/bin/sh", "-c", command],
            check=True,
            capture_output=True,
            text=True,
            cwd=ctx.deps.workspace_home,
            env=os.environ.copy(),
        )

        msg = f"Exit code: {result.returncode}\nStdout:\n{result.stdout}\n\nStderr:\n{result.stderr}"
        print(msg)
        return msg
    except subprocess.CalledProcessError as e:
        msg = f"CalledProcessError: {e}"
        print(msg)
        return msg
    except Exception as e:
        print(f"Failed to run command: {e}")
        raise ModelRetry(f"Failed to run command: {e}")
