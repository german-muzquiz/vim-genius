# Tasks

- [x] Create `tests/genius_assistant` directory for backend unit tests.
- [x] Configure pytest and pytest-asyncio in `pyproject.toml` (or requirements).
- [x] Add skeleton test files for core modules:
  - `tests/genius_assistant/test_main.py`
  - `tests/genius_assistant/test_config.py`
  - `tests/genius_assistant/test_context.py`
  - `tests/genius_assistant/test_prompts.py`
  - `tests/genius_assistant/test_schemas.py`
  - `tests/genius_assistant/test_code_blocks.py`
  - `tests/genius_assistant/test_utils.py`
- [x] Add skeleton test files for each tool under `genius_assistant/tools`:
  - `tests/genius_assistant/tools/test_read_file.py`
  - `tests/genius_assistant/tools/test_add_file.py`
  - `tests/genius_assistant/tools/test_edit_file.py`
  - `tests/genius_assistant/tools/test_scan_workspace.py`
  - `tests/genius_assistant/tools/test_check_project.py`
  - `tests/genius_assistant/tools/test_run_tests.py`
  - `tests/genius_assistant/tools/test_web_search.py`
- [ ] In each test file, implement at least:
  - One expected-use case test
  - One edge-case test
  - One failure-case test
- [ ] Run `pytest` to verify test discovery and ensure there are no import or syntax errors.
- [ ] Implement test logic for other modules and tools.

## Discovered During Work

- [x] Save message history to `~/.genius/history/current_run.json` after a turn (2025-05-17)

- [x] Implement tests for read_file tool (`tests/genius_assistant/tools/test_read_file.py`) (2025-05-13)
- [ ] Implement actual test logic for each module and tool, covering public functions and error paths.
- [ ] Mark each task as complete in this file once implemented.
