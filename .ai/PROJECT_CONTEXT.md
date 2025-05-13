# Project Context

This document provides an overview of the **vim-genius** project, describing its vision, architecture, technology stack, operational constraints, and developer workflows.

---

## 1. High-Level Vision

**vim-genius** is an AI-powered code-assistant plugin for Vim/Neovim that delivers context-aware editing, code generation, and automated refactoring directly within the editor. By combining a lightweight Vimscript frontend with a Python-driven AI backend, developers can select code blocks, issue natural-language commands, and receive in-place edits, suggestions, or explanations without leaving their editing session.

- Purpose: Embed AI-driven workflows—code completion, refactoring, documentation, and test scaffolding—into Vim/Neovim to boost productivity.
- Target Users: Vim/Neovim enthusiasts, Python developers, and polyglot programmers seeking seamless LLM features in a terminal-centric editor.
- Ecosystem Fit: Complements existing LSP-based workflows by providing generative AI features alongside traditional linters, formatters, and language servers.

---

## 2. Project Architecture

```
vim-genius/
├── Dockerfile                 # Containerized environment for CI and development
├── pyproject.toml             # Dependencies, build, formatting, and lint configuration
├── README.md                  # High-level overview and setup instructions
├── .gitignore
├── .tasks                     # Task runner definitions (lint, type-check, test)
├── vim/                       # Vimscript plugin: core integration and user docs
│   ├── plugin/                # Entrypoint scripts (genius.vim)
│   ├── ftplugin/              # Filetype-specific command mappings
│   ├── ftdetect/              # Filetype detection for plugin activation
│   ├── syntax/                # Syntax highlighting for diffs, history
│   ├── autoload/              # Lazy-loaded helper functions
│   ├── after/                 # Overrides and enhancements
│   └── doc/                   # User documentation (genius.txt)
│
└── genius_assistant/          # Python backend: CLI entrypoint and tools
    ├── main.py                # CLI dispatcher and command definitions
    ├── config.py              # Configuration management (env, API keys)
    ├── context.py             # Context builder (buffer and workspace metadata)
    ├── prompts.py             # Prompt templates and injection logic
    ├── schemas.py             # Pydantic data models for messages and responses
    ├── code_blocks.py         # Diff generation and patch application
    ├── utils.py               # Shared helpers (logging, I/O, error handling)
    └── tools/                 # Modular tool implementations (plugin pattern)
        ├── read_file.py
        ├── add_file.py
        ├── edit_file.py
        ├── scan_workspace.py
        ├── check_project.py
        ├── run_tests.py
        └── web_search.py
```

### Core Components

- **Vimscript Plugin** (`vim/`): Defines Vim commands (`:Genius`, `:GeniusEdit`, `:GeniusExplain`, etc.), handles selections, highlights diffs, and invokes the Python backend via CLI or RPC.
- **Python Backend** (`genius_assistant/`): Processes CLI arguments, gathers editor context, constructs and sends LLM prompts, parses responses, and applies code changes or displays suggestions.
- **Tool Plugins** (`genius_assistant/tools/`): Individual operations (file I/O, linting, testing, web search) registered via decorators for extensibility.
- **Data Models** (`schemas.py`): Pydantic classes ensure type safety when interacting with external APIs and internal logic.

---

## 3. Technology Stack

- **Languages**: Vimscript (plugin layer) and Python 3.12+ (backend services)
- **Package & Build**: Poetry/UV (`pyproject.toml` & `uv.lock`)
- **API Integration**: `pydantic-ai`, `httpx`, `crawl4ai`, `jinja2`
- **Configuration**: `python-dotenv` for environment-based settings
- **Validation**: Pydantic v2 for data schemas
- **Formatting & Lint**: Ruff (configured in `pyproject.toml`), MyPy with `pydantic.mypy` plugin, Pylint for complexity rules
- **Testing**: pytest (including `pytest-asyncio`), Vimscript tests to be added
- **CI/CD**: GitHub Actions or equivalent (Docker-based pipelines for lint, type-check, tests)
- **Task Runner**: `.tasks` (Invoke/Taskfile for common workflows)

---

## 4. Constraints & Limitations

- **Editor Support**: Vim 8+ and Neovim (terminal mode). GUI clients may exhibit varying behavior.
- **Performance**: Dependent on LLM API response times and network latency; large buffers or workspaces can introduce overhead.
- **Security**: Requires valid API credentials; code snippets and context are transmitted over the network.
- **Extensibility**: New filetype or feature support may require Vimscript and backend schema updates.
- **Environment**: Python 3.12+ is required. Node or other runtimes are not used.
- **Resource Usage**: LLM token limits and rate limits may apply based on provider.

---

## 5. Build, Lint, and Test

1. Install Dependencies:
   ```bash
   uv sync
   ```

2. Linting & Formatting:
   ```bash
   uv run check-project     # Runs Ruff (--fix) and MyPy
   uv run lint              # Alias for `ruff check .`
   uv run format            # Alias for `ruff fix .`
   ```

3. Type Checking:
   ```bash
   uv run mypy
   ```

4. Testing:
   ```bash
   uv run test              # Runs pytest suite
   pytest                   # Direct invocation
   ```

5. CI Pipeline (GitHub Actions):
   - Steps: Checkout, Setup Python 3.12, `uv sync`, `uv run check-project`, `uv run test`

---

*Last updated: 2025-05-12*