# Changelog

Todas as mudanças notáveis deste projeto são documentadas neste arquivo. O formato é baseado em
[Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/). Este projeto ainda não tem releases
versionados — o desenvolvimento acontece diretamente em `main`, sprint a sprint (ver
[`docs/08-roadmap.md`](./docs/08-roadmap.md)).

## [Unreleased]

### Sprint 9 (fase 1) — Notificações, Recuperação de Senha, Rate Limiting

- Corrigidos 31 testes que estavam quebrados na árvore de trabalho: `IssueService`/
  `CommentService` haviam ganhado um argumento novo (`notification_service`) sem os
  fixtures de teste correspondentes serem atualizados. `features/notifications/`
  ganhou cobertura de teste unitário e de contrato completa (antes zero).
- RF-NOTIF-01/02: notificação in-app de menção (`CommentService._notify_mentions`) e
  de mudança de status de issue (`IssueService._notify_status_change`) — nenhuma das
  duas notifica quando o próprio autor da ação é o destinatário.
- RF-AUTH-06 (recuperação de senha): `POST /auth/password-reset/request` +
  `POST /auth/password-reset/confirm`. Token opaco de 256 bits, hash SHA-256 em
  repouso, uso único, expira em 30 min (`PASSWORD_RESET_TOKEN_EXPIRE_MINUTES`).
  Sempre `202` no `request` independente de o e-mail existir (anti-enumeration) — o
  token nunca é devolvido pela resposta HTTP, diferente do convite de workspace;
  `core/mail.py::MailSenderProtocol` (novo) é o ponto de extensão para um provedor de
  e-mail real. Confirmar o reset revoga todas as sessões ativas do usuário. Ver
  ADR-017 em `docs/09-decision-log.md`.
- Hardening de rate limit por rota: `password-reset/request`/`confirm` no mesmo tier
  de `login`/`register` (5/min por IP); novo tier de 60/min por IP para qualquer
  requisição sem Bearer válido a uma rota protegida (antes não era limitada de jeito
  nenhum).
- Pendente para uma fase 2 desta sprint: métricas básicas (5xx por rota, p95 por
  endpoint) e a revisão de segurança completa do checklist de `docs/07-security.md`.

### Identidade visual — FlowDesk "Ring Gate"

- Marca oficial integrada a partir da spec de produção do design (`brand/Logo.tsx`):
  símbolo em anel com duas barras, geometria travada em grid de 100u, cores de tinta
  `#14130F`/`#FAF8F3` (claro/escuro) sem uso de `filter: invert()`.
- Favicon (`public/favicon.svg`) substituído do placeholder gerado pela marca real,
  com variante clara/escura via `prefers-color-scheme`.
- `Logo` (lockups símbolo/horizontal/vertical) substitui o texto "FlowDesk" solto em
  `Topbar`/`LoginPage`.

### Sprint 8.7 — Production Readiness & Observability

- Envelope de erro padrão estendido a `RequestValidationError` e `HTTPException` do
  Starlette (antes vazavam o formato default do FastAPI em vez de `{"error": {...}}`).
- `GET /health/ready` (novo): checagens reais de banco, Redis e storage, com registro
  extensível para novas dependências (`core/health.py`); `GET /health` permanece liveness
  pura; `GET /version` ganhou `uptime_seconds`. Detalhe de falha (`str(exc)`) só aparece
  na resposta HTTP fora de produção — em produção fica só no log estruturado.
- Logging estruturado agora carrega `user_id` e `environment` em toda linha (além do
  `request_id` já existente); nova linha de access-log (`http_request`) por requisição.
- `SecurityHeadersMiddleware` novo (`X-Content-Type-Options`, `X-Frame-Options`,
  `Referrer-Policy`, `Permissions-Policy`, HSTS em produção); CORS com
  `allow_methods`/`allow_headers` explícitos em vez de `*`.
- `Settings` recusa subir com `ENVIRONMENT=production` usando a chave JWT de
  desenvolvimento; `environment` validado contra um conjunto fechado de valores.
- Docker multi-stage (`development`/`production`) para backend e frontend, agora
  copiando `poetry.lock` no build (antes só `pyproject.toml`, então a imagem podia
  re-resolver dependências fora do que o `pip-audit` do CI auditou);
  `docker-compose.prod.yml` novo demonstrando a topologia de produção. Ambos os
  targets `production` validados com `docker build` nesta sessão.
- CI: `pip-audit`/`npm audit` (não bloqueantes) e um novo job que builda as imagens
  Docker de produção (bloqueante); `.github/dependabot.yml` novo.
- `PRODUCTION_CHECKLIST.md` novo na raiz do repositório.
- Corrigido um bug de tipagem pré-existente em `core/rate_limit.py`: `Redis` (sem
  parâmetro genérico) e um `from_url()` sem retorno anotado — ambos exigem tratamento
  explícito (`Redis` sem `[str]`, `# type: ignore[no-untyped-call]` comentado) contra a
  versão de `redis`/`mypy` de fato pinada em `poetry.lock` (5.3.1 / 1.20.2). `mypy src`
  verde.
- Corrigido `tests/conftest.py::client`: `httpx.ASGITransport` não disparava o lifespan
  do FastAPI, então `app.state.started_at` nunca era setado e `GET /version` quebrava em
  qualquer teste de contrato.

### Sprint 8.6 — Architecture Hardening & Code Quality

- `shared/lib/routes.ts` (route builder único) substitui 11 pontos de template literal
  solto de rota espalhados pelo frontend.
- Code-splitting por rota em `router.tsx` (`React.lazy` + `Suspense`), endereçando o
  chunk único de 760kB da Sprint 8.5.
- `MAX_PICKER_PAGE_SIZE` (`shared/lib/constants.ts`) elimina `per_page: 100` repetido em
  4 arquivos.
- `frontend/.husky/pre-commit` mais defensivo: checa se o `pre-commit` do backend de
  fato executa antes de tentar ativar o venv.
- Barrel exports e múltiplos path aliases (pedidos originalmente) **não** foram
  adicionados — contradiziam decisão já documentada (`docs/05-frontend.md` §1,
  `docs/10-coding-standards.md` §3); ver ADR-015.

### Sprint 8.5 — Frontend Foundation & Design System Preparation

- Design system documentado (`src/design-system/*.md`) e primeiros componentes
  compostos reutilizáveis sob `shared/components/{layout, navigation, typography,
  data-display, forms, overlay, feedback, motion}/`, construídos sobre as primitivas
  shadcn/ui — fundação para a sprint de identidade visual/telas finais não precisar de
  refatoração estrutural.
- `Sidebar`/`Topbar` reescritos: colapsar, menu mobile (`Sheet`), seletor de workspace
  com dado real, breadcrumb estrutural, busca/notificações como pontos de extensão sem
  integração ainda.
- `shared/theme/tokens/*.ts` (um arquivo por categoria) substitui o antigo
  `theme/tokens.ts` único; `shared/stores/uiStore.ts` (primeiro store de UI
  cliente-only); `ErrorBoundary`, `EmptyState`/`ErrorState` (movidos para
  `feedback/`), skeletons genéricos (`PageSkeleton`/`CardSkeleton`/`TableSkeleton`/
  `ListSkeleton`/`KanbanSkeleton`) substituindo duplicação real entre issues/projects.
- Hooks (`useBreakpoint`, `useMediaQuery`, `useDisclosure`, `useLocalStorage`,
  `usePrevious`) e utils (`date.ts`, `string.ts`, `number.ts`, `validation.ts`) novos,
  substituindo duplicação real de formatação em 5 componentes de feature.
- 21 componentes shadcn/ui novos instalados via CLI.

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
