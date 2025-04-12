FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV PYTHONPYCACHEPREFIX=/app-cache/pyc
ENV UV_LINK_MODE=copy

RUN mkdir -p "$PYTHONPYCACHEPREFIX"

WORKDIR /app

COPY pyproject.toml uv.lock /app/

RUN --mount=type=cache,target=/app-cache/uv <<EOF
    uv sync --frozen --compile-bytecode --no-install-project --cache-dir /app-cache/uv
EOF

COPY . /app/

ENTRYPOINT [ "uv", "run" ]
CMD [ "python", "bot.py" ]
