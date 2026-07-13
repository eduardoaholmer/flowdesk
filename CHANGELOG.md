# Changelog

Todas as mudanças notáveis deste projeto são documentadas neste arquivo. O formato é baseado em
[Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/). Este projeto ainda não tem releases
versionados — o desenvolvimento acontece diretamente em `main`, sprint a sprint (ver
[`docs/08-roadmap.md`](./docs/08-roadmap.md)).

## [Unreleased]

### Sprint 1.5 — Bootstrap do repositório e hardening da fundação

- Repositório publicado no GitHub com metadados de projeto open source (LICENSE, CONTRIBUTING,
  CODE_OF_CONDUCT, SECURITY, templates de issue/PR, CODEOWNERS).
- Estrutura do frontend corrigida para bater com `CLAUDE.md` §13: componentes shadcn/ui e
  `utils.ts` movidos para `src/shared/`.
- Stack do frontend atualizada de React 18 (documentado por engano) para React 19 (o que
  realmente estava instalado) — ver `docs/09-decision-log.md` (ADR-003).
- Tooling de teste do frontend (Vitest + Testing Library) instalado e integrado ao CI, fechando
  o gap entre o que `CLAUDE.md` exige e o que existia.
- Hardening: containers de desenvolvimento (backend/frontend) rodando como usuário não-root;
  healthchecks adicionados para os serviços `backend`/`frontend` no Docker Compose;
  `X-Request-ID` validado antes de entrar nos logs estruturados.

### Sprint 0-1 — Fundação

- Monorepo (`backend/`, `frontend/`, `docs/`) com backend FastAPI e frontend React/Vite de pé,
  sem regra de negócio.
- Camadas transversais do backend (`core/`): configuração, sessão de banco (SQLAlchemy async),
  hierarquia de exceções de domínio, logging estruturado (structlog), middleware de
  request-id/CORS.
- Alembic configurado para migrações assíncronas.
- Shell do frontend: roteamento (React Router), providers (TanStack Query, tema claro/escuro),
  layout base (Sidebar/Topbar), componentes shadcn/ui.
- Docker Compose (Postgres 16, Redis 7, backend, frontend) e CI (GitHub Actions) rodando
  lint/format/type-check/testes em cada PR.
- Documentação completa do produto e da arquitetura em `docs/`.
