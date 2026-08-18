FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml ./
COPY uv.lock ./
COPY src ./src
COPY main.py ./

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir uv && \
    uv sync --frozen --no-dev

EXPOSE 8000

CMD ["uv", "run", "python", "main.py"]
