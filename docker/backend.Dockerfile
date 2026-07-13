# Imagem de desenvolvimento — hot reload via volume montado pelo docker-compose.
# Otimização multi-stage para produção fica para uma sprint futura de deploy
# (CLAUDE.md §1.6 — não construímos isso especulativamente agora).
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1

RUN pip install --no-cache-dir poetry==1.8.3

WORKDIR /app

COPY pyproject.toml ./
RUN poetry install --no-root --only main

COPY . .

RUN useradd --create-home --shell /bin/bash --uid 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
