# Multi-stage: `development` (hot reload via volume montado pelo docker-compose, usada
# por padrão em docker-compose.yml) e `production` (imagem imutável, sem bind mount, sem
# dependências de dev, múltiplos workers) — ver docker-compose.prod.yml.
FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1

RUN pip install --no-cache-dir poetry==1.8.3

WORKDIR /app

RUN useradd --create-home --shell /bin/bash --uid 1000 appuser

COPY pyproject.toml poetry.lock ./

FROM base AS development

RUN poetry install --no-root --only main,dev

COPY . .
RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

FROM base AS production

RUN poetry install --no-root --only main

COPY . .
RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# `--workers` fixo (não dinâmico via shell) para manter a imagem imutável e o
# comportamento previsível entre ambientes — ajustar exige uma nova imagem, não uma
# variável de ambiente lida em runtime (CLAUDE.md §1.6, evita configurabilidade
# especulativa além do que este projeto de portfólio precisa hoje).
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
