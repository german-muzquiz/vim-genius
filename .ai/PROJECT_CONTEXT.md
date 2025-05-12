# Project Context

This document provides an overview of the **vim-genius** project, describing its vision, architecture, technology stack, and operational constraints.

---

## 1. High-Level Vision

**vim-genius** is an AI-powered code-assistant plugin for Vim/Neovim that brings advanced code intelligence (such as context-aware editing, code generation, and automated refactoring) directly into the editor. By coupling a lightweight Vimscript frontend with a Python-driven AI backend, it allows developers to interact with large language models (LLMs) seamlessly: selecting code blocks, issuing natural-language commands, and receiving in-place edits or suggestions without leaving their editing session.

- *Purpose*: Enhance developer productivity by embedding AI-driven workflows (code completion, refactoring, documentation, testing scaffolding) into Vim.
- *Target Users*: Vim/Neovim enthusiasts, Python developers, and polyglot programmers seeking a tight integration of LLM capabilities in a terminal-centric editor.
- *Ecosystem Fit*: Complements existing LSP-based workflows by providing generative AI features, can be used alongside or as an extension to language servers and traditional linters/formatters.

---

## 2. Project Architecture

```
vim-genius/
├── Dockerfile
├── pyproject.toml        # Dependencies, code style and lint configuration
├── README.md
├── .gitignore
├── .tasks                # Task runner definitions (lint, test, package)
├── vim/                  # Vimscript plugin: core integration and docs
│   ├── plugin/           # Entrypoint scripts (genius.vim)
│   ├── ftplugin/         # Filetype-specific bindings for genius commands
│   ├── ftdetect/         # Auto-detect filetypes for plugin activation
│   ├── syntax/           # Syntax highlighting for plugin artifacts (diffs, history)
│   ├── autoload/         # Lazy-loaded helper functions
│   ├── after/            # Overrides and syntax enhancements
│   └── doc/              # User documentation (genius.txt)
│
└── genius_assistant/     # Python backend: CLI entrypoint and tool implementations
    ├── main.py           # CLI entrypoint and dispatcher
    ├── config.py         # Configuration management (API keys, timeouts)
    ├── context.py        # Context builder (collects buffers, file metadata)
    ├── prompts.py        # Prompt templates and injection logic
    ├── schemas.py        # Pydantic models for messages, code blocks, API responses
    ├── code_blocks.py    # Abstractions for diff generation and patch application
    ├── utils.py          # Shared helper functions (logging, I/O)
    └── tools/            # Individual tool implementations following a plugin pattern
        ├── read_file.py
        ├── add_file.py
        ├── edit_file.py
        ├── scan_workspace.py
        ├── check_project.py
        ├── run_tests.py
        └── web_search.py
```

### Core Components

- **Vimscript Plugin** (`vim/`): Exposes user commands (e.g., `:GeniusEdit`, `:GeniusExplain`) and handles selection, highlighting of diffs, and invoking the Python backend via RPC/CLI.
- **Python Backend** (`genius_assistant/`): Parses CLI arguments, collects editor context, constructs prompts, calls LLM APIs, processes and formats responses, and applies edits or outputs suggestions.
- **Tool Plugins** (`genius_assistant/tools/`): Modular commands that implement low-level operations (file I/O, test execution, linting, workspace scanning, web search) following a decorator-based registration pattern.
- **Data Models** (`schemas.py`): Validated classes for request/response payloads, ensuring type-safety and consistency when interacting with LLM services.

---

## 3. Technology Stack

- **Programming Languages**: 
  - Vimscript (plugin layer)  
  - Python 3.9+ (backend services)
- **Package & Build**: UV (`pyproject.toml`)
- **Data Validation**: Pydantic (type-safe models for messages, responses)
- **LLM Integration**: Pydantic AI compatible with a wide range of LLMs
- **Task Automation**: `.tasks` (Invoke/Taskfile for linting, formatting, testing workflows)
- **Formatting & Style**: Ruff (configured via `pyproject.toml`)
- **Testing**: pytest (unit and integration tests for Python backend), Vimscript tests (TBD)  
- **CI/CD**: GitHub Actions (recommended) or equivalent; containerized lint/test pipeline via Docker

---

## 4. Constraints & Limitations

- **Editor Compatibility**: Supports Vim 8+ and Neovim in terminal mode; GUI clients may have varying behavior.
- **Performance**: Latency depends on LLM API response times and network speed; large buffers or projects can introduce overhead.
- **Security**: Requires API credentials for LLM services; sensitive code is sent over the wire.
- **Extensibility**: Plugin system loosely coupled but adding new filetype integrations may require additional Vimscript.
- **Environment**: Python 3.9+ required

