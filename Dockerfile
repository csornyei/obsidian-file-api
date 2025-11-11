FROM python:3.13-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV BASE_FOLDER=/data/app
RUN mkdir -p $BASE_FOLDER
VOLUME [ "$BASE_FOLDER" ]

WORKDIR /app

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project

ADD . /app

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked

CMD ["uv", "run", "fastapi", "run", "--host", "0.0.0.0", "--port", "8000", "app/main.py"]