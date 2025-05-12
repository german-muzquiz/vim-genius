"""
Tool that runs automated tests for the current project.
"""

import os
import subprocess
from typing import Union

from pydantic_ai import ModelRetry, RunContext
from pydantic_ai.tools import ToolDefinition

from genius_assistant.schemas import Deps
from genius_assistant.utils import load_tasks_config


async def prepare_run_tests(ctx: RunContext[Deps], tool_def: ToolDefinition) -> Union[ToolDefinition | None]:
    if not os.path.exists(os.path.join(ctx.deps.workspace_home, ".tasks")):
        return None
    tasks_path = os.path.join(ctx.deps.workspace_home, ".tasks")
    configs = load_tasks_config(tasks_path)
    section = "run-tests"
    if section not in configs:
        return None

    conf = configs[section]
    if "command" not in conf:
        return None

    return tool_def


def run_tests(ctx: RunContext[Deps]) -> str:
    """
    Runs automated tests for the current project.
    This tool is recommended to be run after any modifications to the source code.

    Args:
        ctx: The context object containing the dependencies.

    Returns:
        A string indicating the result of the tests.
    """
    print("=> Running tests ", end="")

    if not os.path.exists(os.path.join(ctx.deps.workspace_home, ".tasks")):
        raise ModelRetry(f"File .tasks does not exist in {ctx.deps.workspace_home}")

    try:
        # Load tasks configuration and extract the check-project settings
        tasks_path = os.path.join(ctx.deps.workspace_home, ".tasks")
        configs = load_tasks_config(tasks_path)
        section = "run-tests"
        if section not in configs:
            return f"Section '{section}' not found in {tasks_path}"

        conf = configs[section]
        if "command" not in conf:
            return f"Command not found in section '{section}' in {tasks_path}"

        command = conf.get("command", "")
        print(f"({command})... ", end="")

        # Remove VIRTUAL_ENV from environment variables for subprocess
        env = os.environ.copy()
        env.pop("VIRTUAL_ENV", None)
        result = subprocess.run(
            ["/bin/sh", "-c", command],
            check=True,
            capture_output=True,
            text=True,
            cwd=ctx.deps.workspace_home,
            env=env,
        )

        if result.returncode != 0:
            msg = (
                "\nError running tests.\n return code: "
                f"{result.returncode}\nstdout:\n{result.stdout},\nstderr:\n{result.stderr}"
            )
            print(msg)
            return msg

        print("tests ran successfully")
        return "tests ran successfully"
    except subprocess.CalledProcessError as e:
        msg = f"\nError running tests.\n\nstdout:\n{e.stdout},\nstderr:\n{e.stderr}"
        print(msg)
        return msg
    except Exception as e:
        print(f"Exception running tests: {e}")
        raise ModelRetry(f"Error running tests: {e}")
