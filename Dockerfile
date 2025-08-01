FROM spaneng/doover_device_base AS base_image
LABEL doover.app="true"

## FIRST STAGE ##
FROM base_image AS builder

COPY --from=ghcr.io/astral-sh/uv:0.7.3 /uv /uvx /bin/
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
ENV UV_PYTHON_DOWNLOADS=0

# Install git for cloning repositories
RUN apt update && apt install -y git && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# give the app access to our pipenv installed packages
RUN uv venv --system-site-packages
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-dev

COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev


## SECOND STAGE ##
FROM base_image AS final_image

COPY --from=builder --chown=app:app /app /app
ENV PATH="/app/.venv/bin:$PATH"
CMD ["doover-app-run"]
