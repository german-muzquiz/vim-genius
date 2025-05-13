"""
Main entry point for the vim-genius CLI tool.
"""

import asyncio
import os
import shutil
import sys
import traceback
from datetime import datetime
from typing import Optional, Union

from jinja2 import Template
from pydantic_ai import Agent, Tool
from pydantic_ai.agent import AgentRun
from pydantic_ai.mcp import MCPServerStdio
from pydantic_ai.messages import (
    FinalResultEvent,
    FunctionToolCallEvent,
    FunctionToolResultEvent,
    PartDeltaEvent,
    PartStartEvent,
    TextPartDelta,
)
from pydantic_ai.settings import ModelSettings

from genius_assistant.config import create_model, load_config, validate_config
from genius_assistant.context import inject_context
from genius_assistant.mcp.filesystem import GeniusFilesystemMCP
from genius_assistant.prompts import SYSTEM_PROMPT
from genius_assistant.schemas import Deps
from genius_assistant.tools import (
    backup_file,
    check_project,
    prepare_check_project,
    prepare_run_tests,
    run_tests,
)
from genius_assistant.utils import read_prompt_file

MAX_TOOL_CALLS = 20


def print_usage_summary(usage):
    """Print a summary of token usage."""
    print("")
    print("\n" + "-" * 81)
    print("Token Usage Summary:")
    print(f"  Requests: {usage.requests}")
    if usage.request_tokens is not None:
        print(f"  Request tokens: {usage.request_tokens}")
    if usage.response_tokens is not None:
        print(f"  Response tokens: {usage.response_tokens}")
    if usage.total_tokens is not None:
        print(f"  Total tokens: {usage.total_tokens}")
    print("-" * 81)


def _get_mcp_servers(workspace_home: str) -> list[MCPServerStdio]:
    servers = [
        GeniusFilesystemMCP(
            "npx",
            args=[
                "-y",
                "@modelcontextprotocol/server-filesystem",
                workspace_home,
            ],
        ),
        MCPServerStdio("uvx", args=["mcp-server-fetch"]),
    ]
    if os.getenv("BRAVE_API_KEY"):
        servers.append(
            MCPServerStdio(
                "npx",
                args=["-y", "@modelcontextprotocol/server-brave-search"],
                env={"BRAVE_API_KEY": os.getenv("BRAVE_API_KEY", "")},
            )
        )
    return servers


def _handle_event(
    event: Union[PartStartEvent, PartDeltaEvent, FinalResultEvent, FunctionToolCallEvent, FunctionToolResultEvent],
    deps: Deps,
) -> Optional[str]:
    if isinstance(event, FunctionToolCallEvent):
        deps.tool_invocations += 1
        if deps.tool_invocations > MAX_TOOL_CALLS:
            raise Exception("Too many tool invocations, aborting")
        args = event.part.args
        if event.part.tool_name == "edit_file":
            print(f"Type of args: {type(args)}")
        print(f"==> Running {event.part.tool_name} ({args})")
        return None
    if isinstance(event, FunctionToolResultEvent):
        return None
    if isinstance(event, PartStartEvent) and event.part.part_kind == "text":
        return event.part.content
    elif isinstance(event, PartDeltaEvent) and isinstance(event.delta, TextPartDelta):
        return event.delta.content_delta
    return None


async def _process_agent_run(run: AgentRun[Deps, str], deps: Deps):
    """
    Process the streaming events from the agent, buffering text chunks until newline
    before printing, to support streaming output line by line.
    """
    buffer = ""
    async for node in run:
        if not Agent.is_model_request_node(node) and not Agent.is_call_tools_node(node):
            continue

        async with node.stream(run.ctx) as request_stream:
            async for event in request_stream:
                msg = _handle_event(event, deps)
                if msg:
                    buffer += msg
                    if "\n" in buffer:
                        lines = buffer.split("\n")
                        for line in lines[:-1]:
                            print(line)
                        buffer = lines[-1]


async def main(workspace_home: str) -> None:
    """Main entry point of the program."""
    if not os.path.isdir(workspace_home):
        raise FileNotFoundError(f"Workspace {workspace_home} not found or is not a directory")

    # Reset backup folder before agent run
    backup_root = os.path.expanduser("~/.genius/backup")
    if os.path.exists(backup_root):
        shutil.rmtree(backup_root)
    os.makedirs(backup_root, exist_ok=True)

    prompt = read_prompt_file()
    load_config()

    if not prompt:
        print("No prompt given")
        sys.exit(1)

    user_prompt = await inject_context(prompt, workspace_home)
    validate_config()
    model_api_family = os.getenv("API_FAMILY", "")
    model_name = os.getenv("MODEL_NAME", "")
    model_api_key = os.getenv("MODEL_API_KEY", "")

    # print("User prompt:")
    # print("\n".join(user_prompt))  # type: ignore

    try:
        tools: list[Tool[Deps]] = [
            # Tool(edit_file, takes_ctx=True),
            # Tool(add_file, takes_ctx=True),
            # Tool(scan_workspace, takes_ctx=True),
            # Tool(read_file, takes_ctx=True),
            Tool(check_project, prepare=prepare_check_project, takes_ctx=True),
            Tool(run_tests, prepare=prepare_run_tests, takes_ctx=True),
            # Tool(web_search, prepare=prepare_web_search, takes_ctx=True),
            Tool(backup_file, takes_ctx=True),
        ]

        # Create the agent
        agent = Agent(
            create_model(model_api_family, model_name, model_api_key),
            system_prompt=Template(SYSTEM_PROMPT).render(date=datetime.now().strftime("%Y-%m-%d")),
            deps_type=Deps,
            result_type=str,
            retries=2,
            tools=tools,
            mcp_servers=_get_mcp_servers(workspace_home),
        )

        print("")
        print("-" * 81)
        print(f"Model: {model_name}")
        print("-" * 81)

        deps = Deps(brave_api_key=os.getenv("BRAVE_API_KEY"), workspace_home=workspace_home)

        async with agent.run_mcp_servers():
            async with agent.iter(
                user_prompt,
                deps=deps,
                model_settings=ModelSettings(max_tokens=8192, temperature=0.0),
            ) as run:
                await _process_agent_run(run, deps)

                # Print the complete response
                # print(result.output)

                # # Extract and process code blocks
                # code_blocks = extract_code_blocks(result.output)
                # if code_blocks:
                #     process_code_blocks(code_blocks, workspace_home)
                if run.result:
                    print_usage_summary(run.result.usage())

        print("")
        print("-" * 81)
        print("User Turn")
        print("-" * 81)
        print("")
    except Exception as e:
        # Handle any exceptions that occur during LLM execution
        print(f"\n\n❌ Error: {str(e)}")
        traceback.print_exc()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="vim-genius CLI")
    parser.add_argument("workspace", help="Path to workspace directory")
    args = parser.parse_args()

    workspace_home = args.workspace
    # Run main with init flag if provided
    asyncio.run(main(workspace_home))
