FROM python:3.12
COPY --from=ghcr.io/astral-sh/uv:0.5.4 /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1
ENV UV_PROJECT_ENVIRONMENT=/usr/local/

WORKDIR /code

# Copy files defining dependencies
COPY pyproject.toml /code/pyproject.toml
COPY uv.lock /code/uv.lock

# Install dependencies
RUN uv lock --upgrade && \
    uv sync --frozen --no-cache --no-install-project --no-editable --no-group dev

# Copy source code
COPY ./app /code/app

