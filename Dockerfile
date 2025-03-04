FROM python:3.12
COPY --from=ghcr.io/astral-sh/uv:0.5.4 /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1
ENV UV_PROJECT_ENVIRONMENT=/usr/local/

WORKDIR /code

# Copy files defining dependencies
COPY pyproject.toml /code/pyproject.toml
COPY uv.lock /code/uv.lock

# Install dependencies
RUN uv sync --frozen --no-install-project --no-editable --no-group dev

# craw4ai prerequisites
RUN crawl4ai-setup

# Copy source code
COPY ./vim_genius /code/vim_genius

# Install source code
RUN uv pip install --system .
