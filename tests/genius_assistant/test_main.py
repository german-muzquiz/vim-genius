"""
Unit tests for genius_assistant.main module.
"""
import pytest
from pydantic_ai.messages import (
    FunctionToolCallEvent,
    FunctionToolResultEvent,
    PartDeltaEvent,
    PartStartEvent,
    TextPartDelta,
)

from genius_assistant.main import _handle_event, print_usage_summary
from genius_assistant.schemas import Deps


def test_print_usage_summary(capsys):
    class Usage:
        requests = 1
        request_tokens = 10
        response_tokens = 20
        total_tokens = 30

    print_usage_summary(Usage)
    captured = capsys.readouterr()
    assert "Requests: 1" in captured.out
    assert "Request tokens: 10" in captured.out
    assert "Response tokens: 20" in captured.out
    assert "Total tokens: 30" in captured.out


def create_tool_call_event(tool_name, args):
    from pydantic_ai.agent import Part
    part = Part(tool_name=tool_name, args=args, part_kind="tool")
    return FunctionToolCallEvent(part=part)


def test_handle_event_function_tool_call_exceeds(monkeypatch):
    deps = Deps(brave_api_key=None, workspace_home=".")
    deps.tool_invocations = 20
    event = create_tool_call_event("edit_file", {"path": "file.py"})
    with pytest.raises(Exception):
        _handle_event(event, deps)


def test_handle_event_text_part_start_and_delta():
    deps = Deps(brave_api_key=None, workspace_home=".")
    part = PartStartEvent(part_kind="text", content="hello")
    msg = _handle_event(part, deps)
    assert msg == "hello"
    delta = PartDeltaEvent(delta=TextPartDelta(content_delta=" world"))
    msg2 = _handle_event(delta, deps)
    assert msg2 == " world"


def test_handle_event_other_events():
    deps = Deps(brave_api_key=None, workspace_home=".")
    event = FunctionToolResultEvent(part=None, result=None)
    msg = _handle_event(event, deps)
    assert msg is None

