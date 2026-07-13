# 08 — Roadmap

Cada sprint tem Definition of Done (DoD) própria, mas todas herdam a DoD-base a seguir — nenhuma sprint é considerada concluída sem ela:

**DoD-base (aplicável a toda sprint):**
- Checklist de `CLAUDE.md` §18 satisfeito para cada tarefa da sprint.
- Lint, format, type-check e suíte de testes (unit + integration + contract das features tocadas) passando em CI.
- Documentação afetada (`docs/03-database.md`, `docs/04-api-design.md`, `docs/09-decision-log.md`) atualizada no mesmo conjunto de PRs da sprint.
- Nenhuma regressão manual observada nos fluxos críticos já existentes (testados via Playwright a partir da Sprint 3, manualmente antes disso).

---

## Sprint 0 — Planejamento e Arquitetura (concluída neste documento)

- **Objetivo**: produzir a fonte de verdade de arquitetura, produto e padrões antes de qualquer código.
- **Entregas**: `CLAUDE.md` + `docs/00` a `docs/10`.
- **Dependências**: nenhuma.
- **Critérios de aceite**: todos os documentos listados no pedido original existem e são internamente consistentes (contrato de API bate com o modelo de dados, matriz de permissões bate com o RBAC descrito na arquitetura).
- **DoD**: aprovação explícita do usuário antes de iniciar Sprint 1.

## Sprint 1 — Fundação

- **Objetivo**: esqueleto executável das duas aplicações, sem lógica de negócio ainda, com toda a tubulação (CI, lint, testes, containers) funcionando.
- **Funcionalidades**:
  - Monorepo com `backend/`, `frontend/`, `docker/`, `docs/`.
  - `backend/`: FastAPI mínimo (`GET /health`, `GET /version`), config via Pydantic Settings, conexão async com Postgres, Alembic inicializado, estrutura de pastas de `CLAUDE.md` §13 criada.
  - `frontend/`: Vite + React + TypeScript mínimo, Tailwind + shadcn/ui configurados, estrutura de pastas de `CLAUDE.md` §13 criada.
  - Docker Compose (Postgres, Redis, API, Web) para ambiente de desenvolvimento reproduzível (RNF-PORT-01).
  - CI (lint + type-check + testes) rodando em toda PR.
  - Ruff, Mypy, ESLint, Prettier configurados e aplicados.
- **Dependências**: Sprint 0 aprovada.
- **Critérios de aceite**: `docker compose up` sobe os quatro serviços; `GET /health` responde 200; frontend carrega uma página placeholder consumindo `/health`.
- **DoD**: DoD-base + pipeline de CI verde no repositório.

## Sprint 2 — Autenticação e Workspaces

- **Objetivo**: primeiro fluxo de ponta a ponta com todas as camadas de segurança do MVP presentes.
- **Funcionalidades**: RF-AUTH-01 a 05, 07; RF-WS-01 a 05, 07.
- **Dependências**: Sprint 1.
- **Critérios de aceite**:
  - Cadastro, login, refresh, logout funcionando ponta a ponta (frontend + backend), com testes de contrato cobrindo caminho feliz e os erros de `docs/04-api-design.md` §2.
  - Criação de workspace, convite e aceite de membro, troca de papel, remoção — com RBAC aplicado (`docs/07-security.md` §8).
  - Teste de integração comprovando isolamento entre dois workspaces distintos (usuário do workspace A não acessa dado do workspace B mesmo manipulando `workspace_id` na URL).
- **DoD**: DoD-base + teste específico de isolamento multi-tenant obrigatório no PR.

## Sprint 3 — Núcleo de Issues

- **Objetivo**: a funcionalidade central do produto.
- **Funcionalidades**: RF-TEAM-01 a 03; RF-ISSUE-01 a 09.
- **Dependências**: Sprint 2 (precisa de workspace/RBAC prontos).
- **Critérios de aceite**:
  - CRUD de times com workflow configurável.
  - CRUD de issues completo, geração de `number` sequencial por time sem corrida (teste de concorrência simulando criação paralela).
  - Board por status com drag-and-drop e atualização otimista no frontend (RNF-PERF-03).
  - Filtros e busca textual funcionando conforme `docs/04-api-design.md` §5.
  - Versionamento otimista (`If-Match`) testado com um cenário de conflito real (duas edições concorrentes).
- **DoD**: DoD-base + primeiro fluxo E2E Playwright (login → criar time → criar issue → mudar status no board).

## Sprint 4 — Colaboração

- **Objetivo**: recursos que dependem do núcleo de issues já existir.
- **Funcionalidades**: RF-COMMENT-01 a 03; RF-ISSUE-10 (atividade).
- **Dependências**: Sprint 3.
- **Critérios de aceite**: comentários com CRUD e permissões corretas; menção `@usuário` reconhecida e armazenada; log de atividade completo e visível no detalhe da issue, cobrindo ao menos criação, mudança de status, mudança de responsável.
- **DoD**: DoD-base.

## Sprint 5 — Planejamento (Projetos e Ciclos)

- **Objetivo**: camada de planejamento acima da issue individual.
- **Funcionalidades**: RF-PROJ-01; RF-CYCLE-01, 02.
- **Dependências**: Sprint 3 (issues precisam existir para serem agrupadas).
- **Critérios de aceite**: projeto agrupando issues de múltiplos times; ciclo com cálculo de progresso (burndown simples) correto contra dados de teste conhecidos.
- **DoD**: DoD-base.

## Sprint 6 — Polimento e Observabilidade

- **Objetivo**: fechar lacunas de produção real antes de considerar o MVP+ "apresentável".
- **Funcionalidades**: RF-NOTIF-01, 02; RF-AUTH-06 (recuperação de senha); hardening de rate limit por rota; métricas básicas (contagem de erro 5xx por rota, latência p95 por endpoint).
- **Dependências**: Sprints 2–5.
- **Critérios de aceite**: notificação in-app gerada e visível para menção e mudança de status; reset de senha funcional; dashboard mínimo (ainda que só via logs estruturados agregáveis) mostrando latência e taxa de erro por rota.
- **DoD**: DoD-base + revisão de segurança completa do checklist de `docs/07-security.md`.

## Sprint 7+ — Extensões futuras (pós-portfólio)

Não planejadas em detalhe agora (evita over-engineering especulativo, `CLAUDE.md` §1.6); candidatas registradas para não serem esquecidas: integrações externas (GitHub, Slack), colaboração em tempo real via WebSocket, papel `GUEST` completo, anexos de arquivo, command palette avançado, app mobile.
