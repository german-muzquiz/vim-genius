import pytest
from pydantic_ai import ModelRetry

from genius_assistant.schemas import Deps
from genius_assistant.tools.read_file import read_file


class DummyContext:
    """
    Simple context stub with deps attribute.
    """
    def __init__(self, workspace_home: str):
        self.deps = Deps(workspace_home=workspace_home)


def test_expected_use_case(tmp_path):
    # Create a temporary file with content
    file_path = tmp_path / "example.txt"
    content = "Hello, Vim Genius!"
    file_path.write_text(content)

    # Use relative filename
    ctx = DummyContext(str(tmp_path))
    result = read_file(ctx, "example.txt")
    assert result == content

    # Use absolute path
    result_abs = read_file(ctx, str(file_path))
    assert result_abs == content


def test_edge_case_empty_file(tmp_path):
    # Create an empty file
    file_path = tmp_path / "empty.txt"
    file_path.write_text("")

    ctx = DummyContext(str(tmp_path))
    result = read_file(ctx, "empty.txt")
    assert result == ""


def test_failure_case_nonexistent(tmp_path):
    # Non-existent file should raise ModelRetry
    ctx = DummyContext(str(tmp_path))
    with pytest.raises(ModelRetry) as exc_info:
        read_file(ctx, "no_such_file.txt")
    assert "does not exist" in str(exc_info.value)
