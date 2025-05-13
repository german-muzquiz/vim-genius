# Tasks

- [ ] Audit the `genius_assistant/` directory to identify dead or unused code (functions, imports, modules).
- [ ] Remove identified dead code and stale tool implementations in `genius_assistant/` and `genius_assistant/tools/`.
- [ ] Review all public functions and classes; add Google style docstrings to ensure proper documentation.
- [ ] Add inline comments and `# Reason:` notes for any non-obvious or complex logic.
- [ ] Create comprehensive unit tests for modules: `context.py`, `prompts.py`, `schemas.py`, `code_blocks.py`, `utils.py`, and each tool in `genius_assistant/tools/`.
- [ ] For each new test, include at least one expected use case, one edge case, and one failure case.
- [ ] Update existing tests to reflect any changes from the code cleanup and refactoring.
- [ ] Ensure the test suite runs cleanly and achieves the desired coverage; update CI configuration if needed.
- [ ] Run `uv run check-project` to verify linting, formatting, and type-checking compliance.
- [ ] Update `README.md` or other documentation if code cleanup affects usage or setup instructions.
- [ ] Mark each task as complete in this file upon finishing.