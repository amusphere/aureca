FROM ghcr.io/astral-sh/uv:python3.12-alpine

WORKDIR /app

# No create venv from uv
ENV UV_SYSTEM_PYTHON=1
ENV UV_PROJECT_ENVIRONMENT=/usr/local/

# Copy project metadata and install dependencies
COPY pyproject.toml .
RUN uv sync

# Copy application code
COPY . .

EXPOSE 8000
CMD ["fastapi", "run", "--host", "0.0.0.0"]
