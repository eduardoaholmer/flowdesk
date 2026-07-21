# 08 — Roadmap

## Milestones (visão executiva, pós-auditoria 2026-07-16)

A partir da conclusão do Milestone 1, o roadmap passa a ser acompanhado em dois níveis: **Milestone** (agrupamento executivo de várias sprints em torno de um objetivo de produto) e **Sprint** (unidade de execução, detalhada seção a seção abaixo). Esta camada não substitui as sprints já registradas — apenas as agrupa retroativamente e ordena o que vem a seguir. A ordem abaixo é uma decisão explícita do usuário que **inverte a prioridade original** de `docs/00-product-vision.md` (que tratava board/Kanban como MVP): o Kanban deixou de ser considerado MVP e passa a ser um milestone grande por si só, só depois de uma base de produto completa e polida.

> **Nota (pós-auditoria de gap, ADR-021)**: o Kanban **não foi removido do produto** — só deixou de fazer parte do MVP/corte inicial. `M5 — Kanban` continua no roadmap como uma feature "premium" construída sobre uma base de produto e de engenharia madura, não descartada. Nenhum trabalho de Kanban começa antes de M4 estar concluído.

- ✅ **M1 — Estabilização** (concluído): Sprints 0–9 fase 1. Notificações, recuperação de senha, hardening de rate limit e estabilização da suíte de testes (ADR-017).
- ✅ **M2 — Product Completeness** (concluído, fase 2 fechada 2026-07-17, ADR-023): transformar o FlowDesk em um produto realmente utilizável antes do Kanban. Fase 1 (Sprint 10, ADR-018) entregou administração de workspace, command palette e a decisão do dashboard (removido). Fase 2 (Sprints 12.1–12.6, ADR-021/ADR-022), aberta após uma auditoria de gap de 2026-07-16, cobriu o que a fase 1 não tocou: correção de UX, revisão de navegação, e — ampliando o escopo original da fase 2 — uma Home/Dashboard real (ADR-022, reverte a Decisão 1 da ADR-018 sob um requisito novo).
- ✅ **M3 — Ring Gate Brand** (concluído, escopo ampliado fechado 2026-07-19, ADR-026): Sprint 11 (ADR-019) entregou a rampa de cor semântica e o motion system CSS-only. O escopo ampliado (Sprint 13.1–13.5, ADR-024/025/026) entregou display font para headings, microinterações de hover, a primeira QA visual em navegador real do projeto e quatro docs de design system novas (Dialogs/Dropdowns/Badges/Empty-Error-Loading States).
- ✅ **M4 — Quality** (concluído, fechado 2026-07-19, ADR-027–032): Playwright (14.4 — primeiro fluxo E2E, achou e corrigiu um bug real em `EditIssueDialog`), MSW + testes de integração de frontend (14.2/14.3), observabilidade/métricas via `GET /metrics` (14.5), revisão de documentação/tooling (14.1), auditoria de segurança completa (14.6 — matriz RBAC conferida sem divergência, dois trade-offs em aberto reafirmados por decisão explícita do usuário). Ver ADR-020/ADR-021 para o detalhamento de escopo herdado da versão anterior deste milestone ("Engineering Quality"); quebra em Sprint 14.1–14.6 e achados da auditoria de gap em ADR-027.
- ✅ **M5 — Kanban** (concluído, fechado 2026-07-20, ADR-033–035): `Team`/`WorkflowState` (schema dormente desde a Sprint 2/ADR-007, nunca removido) mais board com drag-and-drop — o antigo "Núcleo de Issues" original da Sprint 0/4/6 nunca executado nessa forma. Deixou de ser considerado feature inicial de produto (`docs/00-product-vision.md` §5 original) — é agora uma feature premium construída só depois que o sistema inteiro estiver sólido (M2–M4 fechados). Quebrado em fases (Sprint 16.1–16.3): board somente-leitura em escopo de workspace com o status fixo atual (16.1, concluída — `Team` segue dormente), drag-and-drop (16.2, concluída — ADR-034), decisão explícita sobre reativar `Team`/workflow por time (16.3, concluída — mantido escopo de workspace, `Team` segue dormente, ADR-035).
- ✅ **M6 — Production** (concluído, fechado 2026-07-20, ADR-036–041): deploy real, backups, TLS, secrets, CI/CD, infraestrutura, escalabilidade — inclui `MailSender`/`StorageProvider` com implementação real (antes só `LoggingMailSender`/`LocalStorageProvider`) e transferência de propriedade de workspace (nunca implementada antes, ver ADR-009/ADR-018). Quebrado em sub-sprints (17.1–17.5): transferência de propriedade (17.1), `StorageProvider` S3-compatible (17.2), `MailSender` SMTP real (17.3), hardening de CI — Trivy + `.env.production.example` (17.4), e runbook de produção (17.5, `docs/11-production-runbook.md`) para os itens que dependem de infraestrutura real não provisionada por um projeto de portfólio (deploy pipeline, TLS, backups, secret manager, autoscaling, agregação de log) — documentados como decisão/runbook, não implementados como infraestrutura "de mentira" (decisão explícita do usuário, ADR-036).
- 🔄 **M7 — Redesign** (em andamento, aberto 2026-07-20, ADR-044): recriar as 6 telas do produto a partir de um handoff de design de alta fidelidade (`docs/design-handoff/2026-07-20-redesign-gestor/`) sobre a marca Ring Gate já existente — não é identidade nova, é refinamento visual/comportamental do que já existe. Quebrado em sub-sprints, começando pela fundação (tokens + linguagem visual de Status/Prioridade, Sprint 18.1) por ser pré-requisito de várias telas.

---

Cada sprint tem Definition of Done (DoD) própria, mas todas herdam a DoD-base a seguir — nenhuma sprint é considerada concluída sem ela:

**DoD-base (aplicável a toda sprint):**
- Checklist de `CLAUDE.md` §18 satisfeito para cada tarefa da sprint.
- Lint, format, type-check e suíte de testes (unit + integration + contract das features tocadas) passando em CI.
- Documentação afetada (`docs/03-database.md`, `docs/04-api-design.md`, `docs/09-decision-log.md`) atualizada no mesmo conjunto de PRs da sprint.
- Nenhuma regressão manual observada nos fluxos críticos já existentes (testados via Playwright a partir da Sprint 6 — primeiro fluxo E2E, DoD daquela sprint —, manualmente antes disso).

---

## Sprint 0 — Planejamento e Arquitetura (concluída)

- **Objetivo**: produzir a fonte de verdade de arquitetura, produto e padrões antes de qualquer código.
- **Entregas**: `CLAUDE.md` + `docs/00` a `docs/10`.
- **Dependências**: nenhuma.
- **Critérios de aceite**: todos os documentos listados no pedido original existem e são internamente consistentes (contrato de API bate com o modelo de dados, matriz de permissões bate com o RBAC descrito na arquitetura).
- **DoD**: aprovação explícita do usuário antes de iniciar Sprint 1.

## Sprint 1 — Fundação (concluída)

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

## Sprint 1.5 — Bootstrap do Repositório, Auditoria Arquitetural e Hardening da Fundação (concluída)

- **Objetivo**: transformar o repositório local em um projeto profissional publicado no GitHub, auditado contra `CLAUDE.md`/`docs/`, antes de iniciar a modelagem de domínio.
- **Entregas**: repositório público no GitHub com metadados de projeto open source (LICENSE, CONTRIBUTING, CODE_OF_CONDUCT, SECURITY, templates de issue/PR, CODEOWNERS); estrutura do frontend corrigida para bater com `CLAUDE.md` §13; tooling de teste do frontend (Vitest + Testing Library) instalado; hardening de containers (usuário não-root, healthchecks) e do middleware de request-id.
- **Dependências**: Sprint 1.
- **Critérios de aceite**: nenhuma referência a IA/Claude em código ou histórico de commits; todos os commits com a identidade Git local; CI verde ponta a ponta.
- **DoD**: DoD-base + aprovação explícita do usuário antes de iniciar Sprint 2.

## Sprint 2 — Modelagem do Domínio e Banco de Dados (concluída)

- **Objetivo**: projetar e implementar o domínio completo (models, repositories, migrations) que sustenta todas as sprints seguintes — sem autenticação, sem CRUDs, sem endpoints, sem interface.
- **Entregas**: 18 tabelas via SQLAlchemy 2.0 (`User`, `Session`, `RefreshToken`, `Workspace`, `WorkspaceMember`, `Invitation`, `Team`, `TeamMember`, `WorkflowState`, `TeamIssueCounter`, `Project`, `Label`, `Issue`, `IssueLabel`, `Comment`, `ActivityLog`, `Notification`, `Attachment`) organizadas em 9 features; 12 migrations Alembic pequenas e reversíveis; um repository por agregado (`Protocol` + implementação, CLAUDE.md §6); 22 testes de integração contra Postgres real cobrindo criação, relacionamentos e constraints; ER e diagramas de `docs/03-database.md` atualizados; ADR-007 registrando os desvios do desenho original da Sprint 0.
- **Dependências**: Sprint 1.5.
- **Critérios de aceite**: `alembic upgrade head` → `downgrade base` → `upgrade head` sem erro; suíte de testes de integração verde; nenhuma regra de negócio, service ou rota implementada (só schema + acesso a dado).
- **DoD**: DoD-base + aprovação explícita do usuário antes de iniciar Sprint 3.

## Sprint 3 — Autenticação e Autorização

> **Nota (pós-execução)**: o pedido explícito do usuário restringiu esta sprint só a autenticação (`RF-AUTH-*`), sem Workspaces/RBAC — ver ADR-008 (`docs/09-decision-log.md`), Decisão 1. Os itens abaixo relativos a Workspaces/RBAC foram executados na Sprint 4 (renumerada, ver nota abaixo) em vez desta. Critérios de aceite e DoD abaixo refletem o esboço original da Sprint 0; o real executado está em ADR-008.

- **Objetivo**: primeiro fluxo de ponta a ponta com todas as camadas de segurança do MVP presentes, construído sobre o schema já modelado na Sprint 2 (`User`, `Session`, `RefreshToken`, `Workspace`, `WorkspaceMember`, `Invitation`).
- **Funcionalidades**: RF-AUTH-01 a 05, 07; RF-WS-01 a 05, 07; `core/security.py` (hash Argon2id, JWT RS256); `core/authorization.py` (`can()`/`require_permission()`).
- **Dependências**: Sprint 2.
- **Critérios de aceite**:
  - Cadastro, login, refresh, logout funcionando ponta a ponta (frontend + backend), com testes de contrato cobrindo caminho feliz e os erros de `docs/04-api-design.md` §2.
  - Criação de workspace, convite e aceite de membro, troca de papel, remoção — com RBAC aplicado (`docs/07-security.md` §8).
  - Teste de integração comprovando isolamento entre dois workspaces distintos (usuário do workspace A não acessa dado do workspace B mesmo manipulando `workspace_id` na URL).
- **DoD**: DoD-base + teste específico de isolamento multi-tenant obrigatório no PR.

## Sprint 4 — Multi-Tenancy: Workspaces, Memberships e Convites (executada — substitui o "Núcleo de Issues" abaixo)

> **Nota de renumeração**: o pedido explícito do usuário para esta sprint foi Workspaces/Memberships/Convites (RF-WS-\*, sem RBAC detalhado), não "Núcleo de Issues" como o esboço original da Sprint 0 previa para a 4ª sprint. Mesmo padrão de resolução de divergência das ADR-007/008 (pedido do usuário prevalece). O antigo conteúdo de "Sprint 4 — Núcleo de Issues" passa a **Sprint 6**; as sprints subsequentes deslizam +1 (antiga Sprint 5 → 7, antiga 6 → 8, antiga 7 → 9) — ver seções abaixo, já renumeradas. Detalhamento completo dos desvios em ADR-009 (`docs/09-decision-log.md`).

- **Objetivo**: infraestrutura completa de Workspaces, Memberships e Convites — camada de service/router sobre o schema já modelado na Sprint 2 (`Workspace`, `WorkspaceMember`, `Invitation`), com isolamento multi-tenant reforçado em duas camadas (`docs/07-security.md` §9).
- **Funcionalidades**: RF-WS-01 a 05, 07 (sem RBAC detalhado — `core/authorization.py` fica para a Sprint 5); `POST/GET/PATCH/DELETE /workspaces`; `GET .../members`, `DELETE .../members/me`; `POST/GET .../invitations`, `DELETE .../invitations/{id}`, `POST /invitations/{token}/accept`; `WorkspaceActivityLog` (auditoria); `GET /users/me` com `workspaces[]`.
- **Dependências**: Sprint 3 (autenticação).
- **Critérios de aceite** (todos atendidos, ver ADR-009 para desvios pontuais):
  - Criação de workspace com owner automático, listagem paginada, detalhe, atualização e exclusão (soft delete) funcionando ponta a ponta com testes de contrato.
  - Convite por e-mail com token opaco hasheado e expiração, aceite validando token/expiração/e-mail, cancelamento, listagem — todos cobertos por teste de contrato feliz + erro.
  - Teste de integração/contrato comprovando isolamento entre dois workspaces distintos (não-membro recebe 404 em toda rota `/workspaces/{id}/...`, nunca dado de outro tenant).
  - Activity log registrando criação/atualização/exclusão de workspace, convite enviado/aceito, saída de membro.
- **DoD**: DoD-base + teste específico de isolamento multi-tenant obrigatório no PR + aprovação explícita do usuário antes de iniciar a Sprint 5.

## Sprint 5 — RBAC (Sistema de Permissões)

- **Objetivo**: `core/authorization.py` (`can()`/`PERMISSION_MATRIX`/`Depends(require_permission(...))`, `docs/07-security.md` §8) sobre a base de Workspaces/Memberships da Sprint 4, substituindo as checagens mínimas inline (`_require_member`/`_require_role`, ADR-009 Decisão 4) sem alterar a checagem de posse subjacente.
- **Funcionalidades**: matriz de permissão completa por papel/ação (`docs/07-security.md` §8); `PATCH .../members/{member_id}` (alterar papel) e `DELETE .../members/{member_id}` (remover outro membro), adiados na Sprint 4 (ADR-009 Decisão 5).
- **Dependências**: Sprint 4.
- **Critérios de aceite**: toda rota que precisa de autorização declarada via `Depends(require_permission(...))`, nunca `if` solto no service; matriz de permissões testada linha a linha contra `docs/07-security.md` §8.
- **DoD**: DoD-base + aprovação explícita do usuário antes de iniciar a Sprint 6.

> **Nota (pós-execução)**: executado como planejado, com dois acréscimos além do esboço acima — `core/permissions.py` (catálogo `Permission`) como módulo próprio separado de `core/authorization.py` (matriz + `PermissionService`), e a checagem contextual `require_can_manage_member` (ADMIN não gerencia OWNER) chamada explicitamente pelo service, já que depende de um recurso buscado por `member_id` e não é resolvível só a partir do `workspace_id` do path. Detalhamento completo em ADR-010 (`docs/09-decision-log.md`).

## Sprint 6 — Núcleo de Projetos (concluída — substitui "Núcleo de Issues" abaixo)

> **Nota (pós-execução)**: o pedido explícito do usuário para esta sprint foi a feature de Projetos (RF-PROJ-01), não "Núcleo de Issues" (Team/Issue/Label/WorkflowState) como esta posição do roadmap previa — mesmo padrão de resolução de divergência já usado nas ADR-007/008/009 (`docs/09-decision-log.md`). `Project` já estava modelado desde a Sprint 2 (ADR-007 Decisão 2) e o RBAC necessário (`Permission.PROJECT_*`) já existia desde a Sprint 5 (ADR-010) sem exigir nenhuma mudança. O conteúdo original de "Núcleo de Issues" (objetivo, funcionalidades e critérios de aceite abaixo) permanece pendente, como próximo trabalho de núcleo do produto, ainda não renumerado para uma sprint específica. Detalhamento completo em ADR-011.

- **Entregue**: `features/projects/` completo (router/service/repository/schemas/exceptions) — CRUD de projeto, arquivar/restaurar como transições de estado explícitas e idempotency-guarded, exclusão bloqueada por issues ativas vinculadas, unicidade de nome (case-insensitive) e de slug por workspace (DB + service), `ProjectActivityLog` (auditoria própria, mesmo padrão de `WorkspaceActivityLog`). Duas migrations (`fc0a10c66145`, `0aa72aead06a`). `ProjectStatus` redefinido do placeholder especulativo da Sprint 2 (`PLANNED/IN_PROGRESS/COMPLETED/CANCELED`) para `ACTIVE/ARCHIVED`. Extração de `core/slug.py` (reaproveitado de `WorkspaceService`) e correção de um bug latente de configuração de mapper cross-feature (`db/models_registry.py`).
- **DoD**: DoD-base satisfeita para a entrega de Projetos (lint/type-check/testes verdes; `docs/03-database.md`, `docs/04-api-design.md` e `docs/09-decision-log.md` atualizados no mesmo conjunto de mudanças). O primeiro fluxo E2E Playwright (critério original desta posição) fica para quando "Núcleo de Issues" for de fato executado.

**Conteúdo original desta posição do roadmap (não executado nesta sprint — ver nota acima):**

- **Objetivo**: a funcionalidade central do produto — camada de service/router sobre o schema de `Team`/`Issue`/`Label`/`WorkflowState` já modelado na Sprint 2, agora com RBAC completo (Sprint 5) disponível.
- **Funcionalidades**: RF-TEAM-01 a 03; RF-ISSUE-01 a 09.
- **Dependências**: Sprint 5 (precisa de RBAC pronto).
- **Critérios de aceite**:
  - CRUD de times com workflow configurável.
  - CRUD de issues completo, geração de `number` sequencial por time sem corrida (teste de concorrência simulando criação paralela sobre `TeamIssueCounter`).
  - Board por status com drag-and-drop e atualização otimista no frontend (RNF-PERF-03).
  - Filtros e busca textual funcionando conforme `docs/04-api-design.md` §5.
  - Versionamento otimista (`If-Match`) testado com um cenário de conflito real (duas edições concorrentes).
- **DoD**: DoD-base + primeiro fluxo E2E Playwright (login → criar time → criar issue → mudar status no board).

## Sprint 7 — Núcleo de Issues (executada — substitui "Colaboração" abaixo)

> **Nota (pós-execução)**: o pedido explícito do usuário para esta sprint foi finalmente o Núcleo de Issues (RF-ISSUE-\*), adiado desde a Sprint 4 (ADR-009) e a Sprint 6 (ADR-011) — mesmo padrão de resolução de divergência já usado nas ADRs anteriores. Diferente do esboço original da Sprint 4 (abaixo), o pedido desta sprint **não incluiu** `Team`/`WorkflowState`/board configurável — `Issue` foi implementada desacoplada, com identificador `FD-{number}` por workspace e status como enum fixo. Isso exigiu uma migration que altera a tabela `issues` já criada na Sprint 2 (`team_id`/`status_id` removidos). Detalhamento completo em ADR-012 (`docs/09-decision-log.md`).

- **Entregue**: `features/issues/` completo (router/service/repository/schemas/exceptions/dependencies) — CRUD de issue, identificador automático (`FD-1`, `FD-2`, ...) via `WorkspaceIssueCounter`, busca por título/descrição (full-text, GIN) e por identificador, filtros (projeto/status/prioridade/responsável/criador), ordenação (criação/atualização/prioridade/vencimento/identificador), paginação offset-based, concorrência otimista (`If-Match`/`version`), exclusão com posse-como-exceção (criador ou `ADMIN`+), `ActivityLog` cobrindo criação/edição por campo/mudança de status/mudança de responsável/exclusão. Frontend completo (`features/issues/`): listagem com toolbar/filtros/busca/ordenação/paginação, modais de criação/edição, página de detalhe com timeline de atividade, empty/loading/error states, rota registrada em `src/app/router.tsx` e link na `Sidebar`. Uma migration (`c573b41b553c`). Testes unitários (service + fake repository), de integração (repository + Postgres real) e de contrato (API completa via `httpx`) cobrindo CRUD, RBAC, isolamento multi-tenant, paginação, filtros, busca e ordenação.
- **DoD**: DoD-base satisfeita para a entrega de Issues (lint/type-check/testes verdes nos dois apps; `docs/03-database.md`, `docs/04-api-design.md`, `docs/02-architecture.md`, `docs/06-backend.md`, `docs/05-frontend.md` e `docs/09-decision-log.md` atualizados no mesmo conjunto de mudanças). Fluxo E2E Playwright (critério original desta posição do roadmap) segue pendente — verificação manual ponta a ponta (criar workspace → criar issue → editar status → ver atividade → excluir) feita via browser nesta sprint.

**Conteúdo original desta posição do roadmap (não executado nesta sprint — ver nota acima):**

- **Objetivo**: recursos que dependem do núcleo de issues já existir, sobre o schema de `Comment`/`ActivityLog` da Sprint 2.
- **Funcionalidades**: RF-COMMENT-01 a 03; RF-ISSUE-10 (atividade).
- **Dependências**: Sprint 6.
- **Critérios de aceite**: comentários com CRUD e permissões corretas; menção `@usuário` reconhecida e armazenada; log de atividade completo e visível no detalhe da issue, cobrindo ao menos criação, mudança de status, mudança de responsável.
- **DoD**: DoD-base.

## Sprint 8 — Comentários, Labels e Anexos (executada — substitui "Planejamento (Ciclos)" abaixo)

> **Nota (pós-execução)**: o pedido explícito do usuário ao final da Sprint 7 apontou esta sprint para Comentários, Labels e Anexos (`Comment`/`Label`/`Attachment`, todos já modelados desde a Sprint 2), não para Ciclos como esta posição do roadmap previa originalmente — mesmo padrão de divergência já registrado nas sprints anteriores. Detalhamento completo em ADR-013 (`docs/09-decision-log.md`).

- **Entregue**: `features/comments/` completo (CRUD de comentário em uma issue, detecção/armazenamento de menção `@local-part-do-e-mail` via `CommentMention`, edição/exclusão com posse-como-exceção, paginação offset-based); `features/labels/` completo (CRUD de label do workspace com `description`, aplicar/remover label em uma issue, `LabelActivityLog` para auditoria do ciclo de vida do próprio label, edição/exclusão restrita a `ADMIN`+ sem posse-como-exceção); `features/attachments/` completo (upload/listagem/download/exclusão de anexo em uma issue, `StorageProvider` como ponto de extensão com `LocalStorageProvider` — disco local — como única implementação, validação por lista branca de `Content-Type` + teto de 10 MB, exclusão com posse-como-exceção). Quatro migrations aditivas (`f42ae23f3ec0`, `a7c1d9f0b2e4`, `f5044a958f94`, `3113f34f2a20`). Frontend completo: `IssueDetailView` ganhou as seções Labels (`IssueLabelPicker`), Anexos (`AttachmentList`, upload + download client-side autenticado + exclusão) e Comentários (`CommentList`/`CommentComposer`/`CommentItem`); `LabelsPage` nova, rota própria (`/w/:workspaceSlug/labels`) e link na `Sidebar`. Testes unitários (service + fake repository), de integração (repository + Postgres real) e de contrato (API completa via `httpx`) para as três features.
- **DoD**: DoD-base satisfeita (lint/type-check/testes verdes nos dois apps; `docs/03-database.md`, `docs/04-api-design.md`, `docs/05-frontend.md`, `docs/06-backend.md`, `docs/07-security.md` e `docs/09-decision-log.md` atualizados no mesmo conjunto de mudanças). Verificação manual ponta a ponta (comentar em uma issue com menção, aplicar/remover label, enviar/baixar/excluir anexo) feita via browser nesta sprint.

**Conteúdo original desta posição do roadmap (não executado nesta sprint — ver nota acima):**

- **Objetivo**: camada de planejamento acima da issue individual — modelar `Cycle` (ainda não existe) e o join `Project ↔ Team`, e agrupar issues em ciclos com cálculo de progresso.
- **Funcionalidades**: RF-CYCLE-01, 02.
- **Dependências**: Sprint 6 (issues precisam existir para serem agrupadas; a feature de Projetos já está pronta desde a Sprint 6).
- **Critérios de aceite**: projeto agrupando issues de múltiplos times (via o novo join `Project ↔ Team`); ciclo com cálculo de progresso (burndown simples) correto contra dados de teste conhecidos.
- **DoD**: DoD-base.

## Sprint 8.5 — Frontend Foundation & Design System Preparation (concluída)

- **Objetivo**: preparar a fundação do frontend (design system, layouts, providers, hooks, utils, skeletons, empty states, arquitetura de tema) para que a Sprint de identidade visual e telas finais não precise de refatoração estrutural. Sem tela final, sem regra de negócio nova, sem cor nova — mesmo padrão de inserção "X.5" da Sprint 1.5 (hardening antes de avançar o roadmap).
- **Entregue**: 21 componentes shadcn/ui novos instalados via CLI (`form`→substituído por `field`, `sheet`, `alert`, `tabs`, `popover`, `hover-card`, `scroll-area`, `checkbox`, `radio-group`, `switch`, `command`, `context-menu`, `breadcrumb`, `empty`, `spinner`, `kbd`, entre outros trazidos como dependência); `shared/theme/tokens.ts` (referência tipada aos design tokens, motion como única categoria genuinamente nova); `AuthLayout`/`EmptyLayout` (`LoginPage`/`HomePage` migradas, mesma marcação visual); `Sidebar`/`Topbar` reescritos (colapsar, menu mobile via `Sheet`, grupos de navegação, footer com usuário, seletor de workspace com dado real de `useCurrentUser`, breadcrumb estrutural, busca e notificações sem integração — pontos de extensão explícitos); `shared/stores/uiStore.ts` (primeiro store de UI cliente-only); `shared/components/ErrorBoundary.tsx`; `shared/components/EmptyState.tsx` e `shared/components/skeletons/` (`PageSkeleton`, `CardSkeleton`, `TableSkeleton`, `ListSkeleton`, `KanbanSkeleton`) generalizando duplicação real encontrada em `IssuesEmptyState`/`ProjectsEmptyState`/`IssuesListSkeleton`/`ProjectsListSkeleton`; hooks `useBreakpoint`, `useMediaQuery`, `useDisclosure`, `useLocalStorage`, `usePrevious`; utils `date.ts`, `string.ts`, `number.ts`, `validation.ts` (substituindo duplicação real de formatação de data/iniciais em 5 componentes de feature). `features/teams/` deliberadamente **não criado** (Team foi removido do domínio pela ADR-012 — recriar a pasta reintroduziria um conceito descartado); `features/dashboard/` e `features/settings/` criados como placeholders documentados.
- **Dependências**: Sprint 8.
- **Critérios de aceite**: nenhuma funcionalidade existente quebrada (auth, workspaces, issues, projects, labels, comments, attachments seguem funcionando); lint, type-check, testes e build verdes.
- **DoD**: DoD-base + `docs/05-frontend.md`, `docs/02-architecture.md` e `docs/09-decision-log.md` (ADR-014) atualizados no mesmo conjunto de mudanças; verificação manual ponta a ponta via browser (login, onboarding, navegação com sidebar colapsada/mobile, logout, tema).

## Sprint 8.6 — Architecture Hardening & Code Quality (concluída)

- **Objetivo**: elevar a qualidade de produção do projeto (organização, consistência, performance, DX) nos dois apps — sem funcionalidade nova, sem alterar schema de banco, sem quebrar comportamento. Precedida por uma auditoria completa (frontend, backend, CI, Docker, config de root) antes de qualquer alteração.
- **Entregue**: `shared/lib/routes.ts` (route builder único, elimina 11 pontos de template literal solto de rota); code-splitting por rota em `router.tsx` (`React.lazy` + `Suspense`, endereça o chunk único de 760kB flagado na Sprint 8.5); `MAX_PICKER_PAGE_SIZE` (`shared/lib/constants.ts`, elimina `per_page: 100` repetido em 4 arquivos); `frontend/.husky/pre-commit` mais defensivo (checa se o `pre-commit` do backend de fato executa antes de tentar ativar o venv, em vez de travar). Dois pedidos do enunciado original — barrel exports (`index.ts` por módulo) e múltiplos path aliases (`@shared/`, `@features/`) — **não foram implementados**: contradiziam decisão já documentada e deliberada (`docs/05-frontend.md` §1, `docs/10-coding-standards.md` §3, alias único `@/` já consistente); confirmado com o usuário, registrado em ADR-015. Backend: nenhuma mudança de código — auditoria não encontrou `print()`, `except Exception` silencioso, dependência não usada, ou inconsistência de `code`/`Protocol` que justificasse alteração.
- **Dependências**: Sprint 8.5.
- **Critérios de aceite**: nenhum comportamento observável mudou; lint, type-check, testes e build (frontend) verdes; build gera múltiplos chunks por rota em vez de um único.
- **DoD**: DoD-base + `docs/09-decision-log.md` (ADR-015) e `docs/02-architecture.md` atualizados no mesmo conjunto de mudanças.

## Sprint 8.7 — Production Readiness & Observability (concluída)

- **Objetivo**: preparar o projeto para um ambiente de produção profissional — confiabilidade, observabilidade, segurança, monitoramento e DX — sem funcionalidade de produto, tela ou mudança de schema. Precedida por uma auditoria completa (`core/`, `main.py`, Docker, CI, `.env.example`, docs) que encontrou uma base já sólida de sprints anteriores; o trabalho foi fechar gaps concretos, não reconstruir observabilidade do zero (detalhamento completo, gap a gap, em ADR-016).
- **Entregue**: envelope de erro padrão estendido a `RequestValidationError`/`StarletteHTTPException` (antes vazavam o formato default do FastAPI/Starlette); `core/health.py` (registro extensível de checagens) + `GET /health/ready` (banco/Redis/storage, 503 se degradado) — `GET /health` liveness inalterado; `user_id`/`environment` em todo log estruturado (`core/logging.py`) via o mesmo padrão de `contextvar` já usado por `request_id`; `AccessLogMiddleware` (linha `http_request` por requisição) e `SecurityHeadersMiddleware` (`X-Content-Type-Options`/`X-Frame-Options`/`Referrer-Policy`/`Permissions-Policy`/HSTS condicional) novos em `core/middleware.py`; CORS com `allow_methods`/`allow_headers` explícitos (era `*`); `Settings.environment` como `Literal` + `model_validator` que recusa subir em produção com a chave JWT de desenvolvimento; Docker multi-stage (`development`/`production`) para os dois apps, `docker-compose.prod.yml` novo (standalone) demonstrando a topologia de produção; CI com `pip-audit`/`npm audit` (não bloqueantes) e um novo job `docker` (bloqueante) validando o build das imagens de produção; `.github/dependabot.yml` novo; `PRODUCTION_CHECKLIST.md` novo na raiz. Um bug de tipagem pré-existente (`core/rate_limit.py`, `Redis` não parametrizado) encontrado e corrigido durante a auditoria.
- **Dependências**: Sprint 8.6.
- **Critérios de aceite**: nenhum comportamento de produto mudou; lint, type-check e testes verdes nos dois apps; `docker build --target production` funcional para os dois Dockerfiles (validado via novo job de CI); `/health/ready` reportando `ok` com Postgres/Redis reais.
- **DoD**: DoD-base + `docs/06-backend.md`, `docs/07-security.md`, `docs/02-architecture.md` e `docs/09-decision-log.md` (ADR-016) atualizados no mesmo conjunto de mudanças.

## Sprint 9 — Polimento e Observabilidade (em andamento — fase 1 concluída)

- **Objetivo**: fechar lacunas de produção real antes de considerar o MVP+ "apresentável". `Notification` já está modelada desde a Sprint 2.
- **Funcionalidades**: RF-NOTIF-01, 02; RF-AUTH-06 (recuperação de senha); hardening de rate limit por rota; métricas básicas (contagem de erro 5xx por rota, latência p95 por endpoint).
- **Dependências**: Sprints 3–8.
- **Critérios de aceite**: notificação in-app gerada e visível para menção e mudança de status; reset de senha funcional; dashboard mínimo (ainda que só via logs estruturados agregáveis) mostrando latência e taxa de erro por rota.
- **DoD**: DoD-base + revisão de segurança completa do checklist de `docs/07-security.md`.

> **Nota (pós-execução, fase 1)**: uma auditoria completa do repositório (2026-07-16) encontrou esta sprint com `features/notifications/` já parcialmente implementada (router/service/schemas/repository) mas não commitada, quebrando 31 testes de outras features (`IssueService`/`CommentService` haviam ganhado um argumento novo — `notification_service` — sem os fixtures de teste correspondentes serem atualizados). Fase 1 (este conjunto de mudanças) fechou: (1) correção dos fixtures quebrados + testes unitários/contrato completos para `NotificationService` (cobertura que faltava inteiramente); (2) RF-NOTIF-01/02 — notificação de menção (`CommentService._notify_mentions`) e de mudança de status (`IssueService._notify_status_change`), ambas sem notificar auto-ação; (3) RF-AUTH-06 (recuperação de senha) via `MailSender`, ver ADR-017; (4) hardening de rate limit por rota, mesma ADR-017. **Pendente para uma fase 2**: métricas básicas (contagem de erro 5xx por rota, latência p95 por endpoint) e a revisão de segurança completa do checklist de `docs/07-security.md` que a DoD desta sprint exige — não cobertas nesta fase.

## Sprint 10 — M2: Frontend Product Completeness (concluída)

- **Objetivo**: fechar o produto frontend antes de introduzir Kanban (M5) — decisão explícita do usuário de inverter a ordem original do roadmap (`docs/00-product-vision.md` §5 tratava board como MVP; deixou de ser). Precedida por uma auditoria completa (frontend atual vs. visão de produto, requisitos, roadmap, ADRs) que encontrou: administração de workspace sem nenhuma UI apesar do backend completo desde as Sprints 4/5; command palette só como casca visual (Sprint 8.5, sem busca real nem atalho de teclado); `features/dashboard/` como placeholder nunca agendado no roadmap; notificações completas no backend (Sprint 9 fase 1) mas Topbar ainda travado no estado vazio da Sprint 8.5.
- **Entregue**:
  - **Administração de workspace** (`features/workspaces/`): `WorkspaceSettingsPage` (abas Geral/Membros/Convites) em `/w/:workspaceSlug/settings`; renomear/mudar slug/descrição e excluir workspace (`OWNER`); convidar por e-mail com papel, copiar o link de aceite (sem envio de e-mail real, mesma limitação já aceita para convite desde a ADR-009) e cancelar convite pendente; alterar papel e remover membro (`OWNER`/`ADMIN`); sair do workspace (própria membership); nova página `/invitations/:token/accept`. Toda ação de mutação é gated client-side pelo papel do usuário (`profile.workspaces[].role`) além da autorização real do servidor (defesa em profundidade, não substituição). **Transferência de propriedade não foi implementada** — nenhum endpoint existe no backend para isso (ADR-009 já registrava como trabalho futuro); ver ADR-018.
  - **Command palette** (`shared/components/command-palette/`): atalho global `Cmd/Ctrl+K` (estado em `uiStore`), navegação por seção do workspace, troca de workspace, tema, logout, busca assíncrona debounced de issues/projetos (reaproveita os endpoints de listagem já existentes — não há endpoint de busca global dedicado), comandos recentes persistidos em `localStorage`. Arquitetura em registro de comandos (`commands.ts`, uma função `buildXCommands` por grupo) pensada para extensão futura sem tocar o componente. Navegação/seleção por teclado vêm de graça do `cmdk` (`ui/command.tsx`), já instalado desde a Sprint 8.5.
  - **Notificações no frontend** (`features/notifications/`): consome os endpoints já entregues na Sprint 9 fase 1 (`GET /notifications`, `PATCH /notifications/{id}`, `POST /notifications/mark-all-read`); `TopbarNotifications` deixa de ser um estado vazio fixo — badge de não lidas, lista com polling (30s), marcar como lida ao abrir, marcar todas como lidas, link direto para a issue relacionada quando aplicável.
  - **Remoção do dashboard**: `features/dashboard/` (placeholder vazio desde a Sprint 8.5, nunca agendado em nenhuma sprint) removido — ver ADR-018 para a análise completa.
- **Dependências**: Sprint 9 fase 1 (workspaces/RBAC desde Sprints 4/5; notificações desde a Sprint 9).
- **Critérios de aceite**: nenhuma regressão nos fluxos existentes; lint, type-check, testes e build do frontend verdes; fluxos novos (convidar → aceitar convite → ver membro na lista; renomear workspace; abrir paleta via atalho e navegar; receber notificação e marcá-la como lida) verificados manualmente via browser.
- **DoD**: DoD-base + `docs/05-frontend.md` e `docs/09-decision-log.md` (ADR-018) atualizados no mesmo conjunto de mudanças + aprovação explícita do usuário antes de iniciar o Milestone 3.

## Sprint 11 — M3: Ring Gate Brand System completion (concluída)

- **Objetivo**: transformar a identidade Ring Gate já aprovada (logotipo/favicon/direção visual, travados desde a integração da marca) em um design system de produção integrado em todo o app — sem redesenhar a identidade, sem inventar conceito novo. Precedida por uma auditoria completa (`frontend/src/design-system/*.md`, toda página/componente/layout/estado) que encontrou o app arquiteturalmente disciplinado (nenhum componente contorna o sistema de tokens com cor hardcoded), mas com a marca existindo só no logotipo — toda a paleta semântica continuava o placeholder acromático do scaffold shadcn — e três pedaços de fundação da Sprint 8.5 nunca adotados: motion (framer-motion, zero call site), `PageContainer`/`ContentContainer` (zero call site), e os tokens `--duration-*`/`--ease-*` (nunca referenciados pelos primitivos Radix).
- **Entregue**: rampa completa de neutros quentes derivada dos dois pontos travados da marca (`--brand-ink`/`--brand-paper`) substituindo o placeholder acromático em toda superfície semântica (`background`/`foreground`/`primary`/`card`/`popover`/`border`/`ring`/`sidebar-*`, dois temas) — `destructive` mantido vermelho puro (funcional, não marca), escurecido em modo claro por contraste (4.49:1→5.3:1, estava abaixo do mínimo AA); `opacity.ts`/`containers.ts` novos (documentam convenção já em uso); `PageContainer` agora envolve `<Outlet/>` em `AppLayout` (toda rota autenticada ganha largura máxima/padding responsivo de uma vez); remoção de `framer-motion` (pacote + os 10 componentes nunca adotados de `shared/components/motion/`) e wiring real dos tokens `--duration-fast/base` nos 8 primitivos Radix que antes hardcodavam `duration-100`/`duration-200`; `prefers-reduced-motion` como regra CSS global única; ícones auditados e já consistentes (nenhuma mudança de código necessária). Documentação (`design-system/{colors,motion,shadow,cards}.md`, `README.md`) atualizada; `docs/09-decision-log.md` (ADR-019) registra as dez decisões completas, incluindo o que foi deliberadamente mantido (não removido) apesar de zero consumidor real (`sidebar-*`/`chart-*`, `ContentContainer`).
- **Dependências**: Sprint 10/M2.
- **Critérios de aceite**: nenhuma cor nova inventada (só a mesma tinta/papel já aprovados); contraste de todo par texto/fundo verificado computacionalmente (WCAG 2.1, OKLCH→sRGB→luminância) e documentado em `colors.md`; lint, type-check, testes e build do frontend verdes.
- **DoD**: DoD-base + `docs/09-decision-log.md` (ADR-019) atualizado no mesmo conjunto de mudanças. **Ressalva**: QA visual em navegador real não foi possível nesta sessão (ambiente sandbox sem as bibliotecas de sistema que o Chromium headless exige, sem acesso a `sudo`) — verificação de contraste feita computacionalmente, não visualmente. Recomendado ao usuário revisar visualmente via `npm run dev` antes de considerar a Fase 7 (QA visual) do milestone definitivamente fechada. Aprovação explícita do usuário necessária antes de iniciar o Milestone 4.

## M2 fase 2 — gap-analysis e quebra em sub-sprints (2026-07-16, ADR-021)

Ao redefinir a ordem oficial de milestones, o usuário manteve M2 aberto (não mais "concluído") e ampliou seu escopo para incluir dois itens que a Sprint 10 não cobriu: correção de pequenos problemas de UX encontrados na implementação, e revisão de toda a navegação do sistema. Antes de qualquer código, uma auditoria de gap (agente read-only, sem edição) revisou administração de workspace, command palette e navegação contra o que de fato existe. Achados completos e a decisão de nomeação (por que "Sprint 12.x" e não "Sprint 2.x") estão em ADR-021. Resumo dos achados que viraram as sub-sprints abaixo:

- **Bug real**: `RequireAuth` já gravava `state:{from:location}` ao redirecionar para `/login`, mas nada lia esse estado — todo login caía sempre em `/`, quebrando silenciosamente o fluxo de "desconectado clica em link de convite → loga → deveria voltar para `/invitations/:token/accept`".
- **Capacidade inacessível**: o backend tem recuperação de senha completa (`POST /auth/password-reset/{request,confirm}`, Sprint 9 fase 1/ADR-017) sem nenhuma rota, página ou link no frontend.
- **Polimento de administração**: listas de membros/convites usam `per_page` fixo de 100 sem paginação real nem o filtro por papel que o backend já suporta; breadcrumb de páginas de detalhe (issue/projeto) mostra o texto literal "Detalhe" em vez do identificador real; `docs/04-api-design.md` diverge do código quanto a quem pode `PATCH` um workspace.
- **Polimento do command palette**: sem indicador de carregamento durante a busca assíncrona, sem tratamento de erro de busca (falha silenciosa vira "nenhum resultado").

> **Nota (ampliação de escopo, 2026-07-16, ADR-022)**: testando o produto como um usuário único, o usuário identificou que `HomePage` — sem nenhum conteúdo, só redirect — faz o produto parecer "vazio" demais para uma tela pós-login. Isso reverte deliberadamente a Decisão 1 da ADR-018 (Sprint 10), que removeu `features/dashboard/` por falta de requisito na época; agora há requisito. Duas sub-sprints novas (12.5/12.6, apendadas após 12.1–12.4 para não reabrir sub-sprints já documentadas — ver ADR-022 Decisão 6) cobrem uma Home/Dashboard real e pragmática, não uma tela de BI.

### Sprint 12.1 — M2: corrigir redirecionamento pós-login (concluída)

- **Objetivo**: corrigir o bug real de maior impacto encontrado na auditoria — login sempre navegava para `/`, ignorando o destino original que `RequireAuth` já preservava em `location.state.from`.
- **Entregue**: `shared/lib/routes.ts::resolveLoginRedirect` (função pura, testada em isolamento) reconstrói o path+querystring do `from` gravado por `RequireAuth`; `LoginPage`/`LoginForm`/`LoginTab` passam a navegar para esse destino após login bem-sucedido (ou permanecem em `/` quando não há um `from`, ex.: acesso direto a `/login`). Testes: unitário de `resolveLoginRedirect` (com/sem `from`, com querystring) e de componente de `LoginForm` (mock do módulo `features/auth/api`, sem rede real — MSW é item de M4, ainda não instalado) cobrindo os dois caminhos de redirecionamento.
- **Dependências**: nenhuma — bug isolado, sem relação com as demais sub-sprints de M2 fase 2.
- **Critérios de aceite**: lint, type-check, testes e build do frontend verdes; login a partir de um link de convite expirado por sessão volta para a página de convite, não para o workspace home.
- **DoD**: DoD-base.

### Sprint 12.2 — M2: recuperação de senha no frontend (concluída)

- **Objetivo**: dar UI ao backend de recuperação de senha (RF-AUTH-06, Sprint 9 fase 1/ADR-017) — hoje uma capacidade de servidor inteiramente inacessível pela interface.
- **Entregue**: `ForgotPasswordPage`/`ForgotPasswordForm` (formulário de e-mail; após um `202` sempre mostra a mesma tela de sucesso, nunca distinguindo e-mail existente de inexistente — anti-enumeration, `docs/07-security.md` §10; erro real de rede/rate-limit continua mostrando um toast, não é tratado como sucesso); `ResetPasswordPage`/`ResetPasswordForm` (formulário de nova senha a partir do `:token` na URL, mesma regra de senha forte do backend — 10+ caracteres, maiúscula/minúscula/número/símbolo — replicada como cópia informativa, validação real fica a cargo do backend; um `401` na confirmação mostra "link inválido ou expirado" com atalho para solicitar um novo, em vez de deixar o usuário reenviar o mesmo formulário sem chance de sucesso); link "Esqueci minha senha" novo em `LoginForm`; rotas `/forgot-password` e `/reset-password/:token` (`routePatterns.resetPassword`/`resetPasswordRoute`, `shared/lib/routes.ts`), ambas lazy-loaded como as demais rotas de produto (Sprint 8.6/ADR-015) em vez de agrupadas no bundle inicial com `LoginPage`, já que não fazem parte do caminho crítico de login. `requestPasswordReset`/`confirmPasswordReset` novos em `features/auth/api.ts`, seguindo o mesmo padrão de `login`/`register` (chamada direta, sem TanStack Query — este é o único módulo `api.ts` do projeto sem sua própria camada `hooks.ts`, convenção já existente antes desta sprint). Cinco testes de componente novos (`ForgotPasswordForm`, `ResetPasswordForm` — sucesso, senha divergente, token inválido).
- **Achado durante a sprint**: os dois testes novos de `ResetPasswordForm` expuseram uma lacuna real de infraestrutura de teste — `tests/setup.ts` não registrava cleanup nem reset de mocks entre `it()`s do mesmo arquivo (`test.globals` não está ligado em `vite.config.ts`, então o auto-cleanup do Testing Library, que depende de `afterEach` estar em `globalThis`, nunca era ativado). Testes anteriores nunca expuseram isso por sorte de padrão de query (texto único por teste) ou por sempre navegarem para longe do form testado. Corrigido com `afterEach(() => { cleanup(); vi.clearAllMocks(); })` — `clearAllMocks` (não `resetAllMocks`) preserva a implementação inicial de mocks definida uma vez no factory de `vi.mock` (padrão já usado por `LoginForm.test.tsx`), zerando só o histórico de chamadas.
- **Dependências**: Sprint 12.1 (mesma área de código, `features/auth/`).
- **Critérios de aceite**: lint, type-check, testes (11 arquivos, 35 testes) e build do frontend verdes; `ForgotPasswordPage`/`ResetPasswordPage` com chunk próprio via code-splitting.
- **DoD**: DoD-base. Mesma ressalva de verificação visual em navegador real das Sprints 12.5/12.6 (Docker inacessível neste sandbox).

### Sprint 12.3 — M2: polimento da administração de workspace e navegação (concluída)

- **Objetivo**: fechar os gaps de polimento encontrados na administração de workspace e corrigir a inconsistência de navegação achada na revisão.
- **Entregue**:
  - **Paginação real + filtro por papel nas listas de membros/convites**: `WorkspaceMembersSettings`/`WorkspaceInvitationsSettings` deixam de buscar `per_page` fixo (100) descartando `meta` — agora usam `Pagination` (o mesmo componente de `IssuesListPage`/`ProjectsListPage`) e um `Select` de papel (`OWNER`/`ADMIN`/`MEMBER`/`GUEST`/"Todos") para membros. `useWorkspaceMembers(workspaceId)` (sem parâmetros, retorna array simples) foi **mantido intocado** — é usado por 4 outros call sites (`IssuesTable`, `IssueFormFields`, `IssueDetailView`, `AttachmentList`, `CommentList`) só para resolver "todos os membros" como lookup por id, não para a tela paginada; `useWorkspaceMembersPage(workspaceId, params)` é um hook novo e separado, evitando alterar a assinatura usada por esses 4 call sites por uma necessidade que não é deles. `useInvitations` (um único call site) foi alterado in-place para aceitar `params`.
  - **Breadcrumb com identificador real**: `Topbar.tsx::TopbarBreadcrumb` busca a issue/projeto em detalhe (`useIssue`/`useProject`, mesma query key da página de detalhe — cache hit na prática, sem round-trip extra) e mostra `identifier`/`name` em vez do texto literal "Detalhe"; um estado de carregamento (`…`) aparece só durante o instante em que o cache ainda não resolveu.
  - **`docs/04-api-design.md` corrigido**: `PATCH /workspaces/{workspace_id}` documentava `OWNER` como único papel autorizado — a matriz real (`core/authorization.py`) sempre concedeu `ADMIN` todas as permissões exceto `WORKSPACE_DELETE`. Código e frontend (`WorkspaceGeneralSettings`) já concordavam entre si; só a tabela divergia. Corrigido para `OWNER`/`ADMIN`, com nota explicando a divergência histórica.
  - **Achado durante a sprint**: dois testes novos (filtro de papel, clique em Select) expuseram outra lacuna de teste — jsdom não implementa `hasPointerCapture`/`setPointerCapture`/`releasePointerCapture`/`scrollIntoView`, que o Radix `Select` chama ao abrir/fechar via clique. `tests/setup.ts` ganhou os polyfills (mesmo padrão já usado ali para `matchMedia`) — sem isso, qualquer teste que interaja com um `Select` via clique falha com `target.hasPointerCapture is not a function`, algo que nenhum teste anterior tinha exercitado.
- **Dependências**: nenhuma nova — usou a base de `features/workspaces/` e `shared/components/layout/` já existente.
- **Critérios de aceite**: lint, type-check, testes (14 arquivos, 43 testes) e build do frontend verdes.
- **DoD**: DoD-base. Mesma ressalva de verificação visual em navegador real das sub-sprints anteriores (Docker inacessível neste sandbox).

### Sprint 12.4 — M2: polimento do command palette (concluída)

- **Objetivo**: fechar os gaps de UX assíncrona do command palette encontrados na auditoria.
- **Entregue**: `CommandPalette.tsx` ganha três estados derivados novos — `isSearching` (`issueResults.isFetching || projectResults.isFetching`, cobre tanto a janela do debounce quanto o round-trip real) mostra "Buscando…" com `Spinner`; `hasSearchError` (`issueResults.isError || projectResults.isError`, só quando não está mais buscando) mostra uma mensagem de erro com botão "Tentar novamente" (`refetch()` de cada query que falhou); `isEmpty` passa a excluir os dois estados acima, então "Nenhum resultado encontrado." não pisca mais durante uma busca em andamento nem mascara uma falha real como se fosse "nada encontrado" (o bug original da auditoria). Dois testes de componente novos (`CommandPalette.test.tsx`) usando promises controláveis manualmente (`deferred()`) para exercitar o estado de carregamento e o de erro+retry sem depender de tempo real de rede.
- **Achado durante a sprint**: mais uma lacuna de teste — `cmdk` (biblioteca por trás do `Command`/`CommandDialog`) usa `ResizeObserver`, que jsdom não implementa; `tests/setup.ts` ganhou um stub mínimo (`observe`/`unobserve`/`disconnect` no-op), mesmo padrão dos polyfills já adicionados nas Sprints 12.2/12.3 (`matchMedia`, APIs de ponteiro do Radix `Select`) — esta é a primeira sprint a montar o `CommandPalette` de fato em um teste.
- **Dependências**: nenhuma — componente isolado (`shared/components/command-palette/`).
- **Critérios de aceite**: lint, type-check, testes (15 arquivos, 45 testes) e build do frontend verdes.
- **DoD**: DoD-base. Mesma ressalva de verificação visual em navegador real das sub-sprints anteriores (Docker inacessível neste sandbox).

### Sprint 12.5 — M2: Dashboard/Home real — fundação, "Minhas issues" e atalhos (concluída)

- **Objetivo**: dar a `HomePage` um destino real em vez de um redirect direto para `/projects` — uma Home pragmática para 1 usuário testando o sistema (issues atribuídas a mim, atalhos rápidos), não uma tela de BI/analytics. Reverte a Decisão 1 da ADR-018 (Sprint 10, dashboard removido por falta de requisito) sob um requisito novo — ver ADR-022 para a análise completa (o que já existia reutilizável, o que faltava, por que a numeração 12.5/12.6 em vez de renumerar 12.2–12.4).
- **Entregue**: rota `/w/:workspaceSlug` nova (`routePatterns.workspaceHome`/`workspaceRoutes.home`, `shared/lib/routes.ts`) — `HomePage` (`/`) passa a redirecionar para ela em vez de `/projects` direto; `features/dashboard/` recriada só com `components/` (`DashboardView`, `MyIssuesWidget`, `QuickActions`), sem `api.ts`/`hooks.ts` próprio — composição pura sobre `useIssues`/`CreateIssueDialog`/`CreateProjectDialog` já existentes, nenhum endpoint novo; widget "Minhas issues" (5 mais recentes atribuídas ao usuário, `useIssues(workspaceId, {assignee_id, sort:"-updated_at", per_page:5})`, com loading/erro/vazio reaproveitando `ListSkeleton`/`ErrorState`/`EmptyState`); atalhos rápidos reaproveitando `CreateIssueDialog`/`CreateProjectDialog` sem nenhum formulário novo; entrada "Início" no `Sidebar` (primeiro item do grupo Workspace) e no command palette (`buildNavigationCommands`); primeiro uso real de `Card`/`CardHeader`/`CardAction`/`CardContent` (shadcn, instalado desde a Sprint 8.5, zero consumidor até agora).
- **Dependências**: nenhuma — não depende de 12.2–12.4 (áreas de código distintas), ortogonal a elas.
- **Critérios de aceite**: lint, type-check, testes (incluindo dois testes de componente novos para `MyIssuesWidget`) e build do frontend verdes; `DashboardPage` com seu próprio chunk via code-splitting (Sprint 8.6/ADR-015).
- **DoD**: DoD-base. **Ressalva**: verificação em navegador real (fluxo autenticado completo) não foi possível nesta sessão — Docker não acessível no sandbox (mesma limitação da ADR-019 para Chromium headless). Recomendado ao usuário validar visualmente via `docker compose up`/`npm run dev` antes de iniciar a Sprint 12.6.

### Sprint 12.6 — M2: Dashboard — atividade recente e projetos ativos (concluída)

- **Objetivo**: completar a Home com os dois widgets identificados na auditoria mas não implementados na 12.5 — atividade recente e projetos ativos.
- **Entregue**: `RecentActivityWidget` (`useRecentNotifications`, filtra client-side por `notification.workspace_id === workspaceId` — o endpoint `GET /notifications` não aceita esse filtro no servidor, ver ADR-022 Decisão 7; reaproveita `NotificationItem`/`useMarkNotificationRead`, os mesmos já usados por `TopbarNotifications`, sem duplicar a lógica de descrição por tipo de notificação nem o estado de "marcar como lida"); `ActiveProjectsWidget` (`useProjects(workspaceId, {status:"ACTIVE", per_page:5, sort:"-updated_at"})`, lista com nome do projeto e data-alvo, empty state reaproveitando `CreateProjectDialog`). Ambos adicionados ao mesmo grid de `DashboardView` da 12.5, sem mudança estrutural na página. Dois arquivos de teste de componente novos (`RecentActivityWidget.test.tsx` cobrindo o filtro por workspace explicitamente, `ActiveProjectsWidget.test.tsx`), mesmo padrão de mock de módulo (sem MSW) já usado por `MyIssuesWidget.test.tsx`.
- **Dependências**: Sprint 12.5 (mesma `features/dashboard/`).
- **Critérios de aceite**: lint, type-check, testes (4 arquivos de teste novos entre 12.5/12.6) e build do frontend verdes; `DashboardPage` cresce de chunk (4.10 kB → 6.15 kB) sem afetar os demais chunks de rota.
- **DoD**: DoD-base. Mesma ressalva de verificação visual em navegador real da Sprint 12.5 (Docker inacessível neste sandbox).

## M2 fechado (2026-07-17, ADR-023)

Com as Sprints 12.1–12.6 concluídas, o usuário aprovou explicitamente o encerramento do Milestone 2 — a última etapa da DoD da Sprint 12.4 (aprovação antes de fechar M2 fase 2). `M2 — Product Completeness` está **concluído** (fase 1 + fase 2, incluindo o Dashboard/Home real que ampliou o escopo original da fase 2). Nenhuma verificação visual em navegador real foi possível em nenhuma sub-sprint desta fase — Docker inacessível em todo o sandbox desta sessão; recomendado ao usuário validar via `docker compose up`/`npm run dev` antes de considerar o milestone visualmente definitivo, mesma ressalva já registrada individualmente em cada sub-sprint.

Isso desbloqueia o planejamento do escopo ampliado de M3 (tipografia, app icon, microinterações, revisão visual completa de todo componente — ADR-021 Decisão 6), que ainda não foi detalhado: mesma disciplina de "não pular etapas" já usada para M2 — o *como* de M3 só é planejado quando o usuário pedir explicitamente para iniciá-lo, não como consequência automática de fechar M2.

## M3 fase 2 — gap-analysis e quebra em sub-sprints (2026-07-18, ADR-024)

Com M2 fechado e a QA visual pendente resolvida, o usuário pediu explicitamente o planejamento do escopo ampliado de M3. Uma auditoria de gap (agente read-only, sem edição) revisou as quatro áreas do escopo — tipografia, app icon, microinterações, revisão visual completa de todo componente — contra o que de fato existe. Achados completos e as decisões de escopo (display font escolhida, app icon fechado sem código) estão em ADR-024. Resumo:

- **Tipografia**: fundação já existe (`Geist Variable`, type scale documentado) — único gap é `--font-heading` ser alias de `--font-sans`. Fraunces (`@fontsource-variable/fraunces`) escolhida como display font para headings.
- **App icon**: `favicon.svg` com a marca Ring Gate já existe, tema-aware — fechado sem código novo (não há requisito de PWA/ícone instalável no roadmap).
- **Microinterações**: o gap mais concreto — zero `hover:scale`/`hover:-translate`/`hover:shadow`/`group-hover` em todo `frontend/src`, cards/linhas de tabela sem nenhum feedback de hover além de cor.
- **Revisão visual completa**: sem Storybook, só viável como passe manual pelas páginas reais do app — a "Fase 7" que a Sprint 11/ADR-019 nunca executou com um humano.

### Sprint 13.1 — M3: display font para headings (concluída)

- **Objetivo**: aplicar `Fraunces` (`@fontsource-variable/fraunces`) como `--font-heading`, resolvendo o placeholder documentado em `design-system/typography.md` (hoje um alias literal de `--font-sans`), mantendo `Geist Variable` como `--font-sans` do corpo.
- **Entregue**: `@fontsource-variable/fraunces` adicionado (`frontend/package.json`); `index.css` importa o pacote e redefine `--font-heading: "Fraunces Variable", serif` (`--font-sans` inalterado); nenhum dos ~10 arquivos que já consomem `font-heading` precisou de ajuste — todos já usavam `font-medium`/`font-semibold`, que mapeiam direto no eixo de peso variável (100–900) do Fraunces; `design-system/typography.md` atualizado removendo a nota de placeholder.
- **Achado durante a sprint**: o container do frontend usa um volume anônimo para `node_modules` (`docker-compose.yml`, isolado do bind mount do código-fonte) — instalar o pacote no host não bastou, foi necessário `docker exec ... npm install` dentro do container. Além disso, o watcher do Vite não detectou a mudança em `index.css` via bind mount no Docker Desktop/Windows (limitação conhecida de propagação de eventos de arquivo em volumes montados), exigindo `docker compose restart frontend` para servir o CSS atualizado — nenhum dos dois é uma mudança de código, só uma nota operacional para as próximas sub-sprints de M3 que também mexerem em assets estáticos.
- **Dependências**: nenhuma — decisão de fonte já registrada na ADR-024, item isolado (`index.css` + import do pacote).
- **Critérios de aceite**: lint, type-check, testes (15 arquivos, 45 testes) e build do frontend verdes; verificação visual em navegador real confirmou Fraunces renderizando em `CardTitle` ("Minhas issues", "Atividade recente") e `DialogTitle` ("Nova issue"), sem erro de console.
- **DoD**: DoD-base + `design-system/typography.md` atualizado.

### Sprint 13.2 — M3: app icon (fechada sem código, ADR-024 Decisão 2)

- **Objetivo**: confirmar formalmente que o favicon Ring Gate já entregue (`favicon.svg`, tema-aware) satisfaz o item "app icon" do escopo ampliado de M3 — sem PWA/manifest, por não haver esse requisito no roadmap.
- **DoD**: só documentação (esta entrada + ADR-024) — nenhuma mudança de código.

### Sprint 13.3 — M3: microinterações (concluída)

- **Objetivo**: adicionar feedback sutil de profundidade/escala/sombra em superfícies interativas (cards, linhas de tabela/lista, itens de navegação) usando os tokens `--duration-*`/`--ease-*` já existentes desde a ADR-019 — sem reintroduzir `framer-motion` (removido na Sprint 11 por zero consumidor real).
- **Entregue**: `ui/card.tsx` ganhou `hover:shadow-sm` + `hover:ring-foreground/15` (intensifica o `ring-foreground/10` de repouso), herdado por todo consumidor (`StatCard`/`InfoCard`, widgets do Dashboard) sem prop nova; `ui/table.tsx::TableRow` ganhou um acento de profundidade à esquerda via `hover:shadow-[inset_2px_0_0_0_var(--primary)]` — `box-shadow inset`, não `border-left`, porque borda lateral em `<tr>` é inconsistente sob `border-collapse` (herdado do preflight do Tailwind); `layout/Sidebar.tsx` (item de navegação inativo) ganhou `hover:translate-x-0.5`. Nenhuma duração/easing nova introduzida — os três reaproveitam o default do Tailwind (150ms), que já coincide com `--duration-base`; `--duration-*`/`--ease-*` continuam consumidos só onde já eram (overlays Radix, ver `motion.md`).
- **Dependências**: nenhuma — usa tokens já existentes, não depende de 13.1/13.2.
- **Critérios de aceite**: `card.tsx` e linhas de `table.tsx`/listas ganham transição visível em hover (não só troca de cor); `prefers-reduced-motion` continua respeitado (regra global já existente, ADR-019); lint, type-check, testes (15 arquivos, 45 testes) e build verdes.
- **DoD**: DoD-base + `design-system/motion.md`/`cards.md`/`shadow.md` atualizados com os novos padrões de hover. **QA visual**: validado em sessão seguinte via `npm run dev` + Chromium headless (backend/Docker seguem indisponíveis neste ambiente, então a validação usou uma página de harness isolada renderizando os componentes reais fora do fluxo autenticado) — os três hovers (`card`, `table-row`, item de nav da sidebar) confirmados via `getComputedStyle` e screenshot em tema claro e escuro. Achado do processo: um dev server pré-existente na porta 5173 servia conteúdo desatualizado (inotify não confiável em `/mnt/c` no WSL) e mascarou os efeitos na primeira tentativa — resolvido subindo um servidor limpo em porta alternativa; não é um bug de produto.

### Sprint 13.4 — M3: revisão visual completa (concluída)

- **Objetivo**: passe manual por todas as páginas reais do app (a "Fase 7" nunca executada da Sprint 11/ADR-019), documentando as categorias de componente ainda sem doc em `design-system/README.md` (Dialogs, Dropdowns, Badges, Empty/Error/Loading States) e produzindo uma lista de achados.
- **Entregue**: primeira QA visual em navegador real (Chromium headless) do projeto — conta de teste + workspace/labels/projects/issues de exemplo criados via UI real contra um backend já em execução no host; todas as páginas autenticadas revisadas em tema claro e escuro (Dashboard, Issues lista/detalhe, Projects lista/detalhe, Labels, Configurações, diálogos de criação/edição, dropdown de workspace, `AlertDialog` de exclusão, `Select` dentro de `Dialog`, viewport mobile). Quatro docs novas: `design-system/{badges,dialogs,dropdowns,empty-error-loading}.md`, indexadas em `design-system/README.md`. Detalhes completos, incluindo a suspeita de bug investigada e descartada (Select dentro de Dialog — falso alarme, ver ADR-025 Decisão 2), em ADR-025.
- **Achados**: (a) `shared/components/forms/FilterBar.tsx` não reflui de forma previsível em mobile (~390px) — botão de ação primária pode ficar espremido ao lado de um filtro; abre Sprint 13.5. (b) `ProjectDetailPage` não lista as issues do próprio projeto (só metadados) — gap de funcionalidade, não de polimento visual; registrado em "Sprint 15+" abaixo, fora do escopo de M3.
- **Dependências**: 13.1/13.3 (revisa o resultado de ambas).
- **Critérios de aceite**: cada página autenticada revisada via `npm run dev` em navegador real; achados documentados; sub-sprints adicionais (13.5+) abertas se necessário, mesmo padrão de apêndice da ADR-022 Decisão 6.
- **DoD**: DoD-base + `design-system/README.md` atualizado.

### Sprint 13.5 — M3: corrige reflow do `FilterBar` em mobile (concluída)

- **Objetivo**: corrigir o achado (a) da Sprint 13.4 — o botão de ação (`actions`) de uma toolbar de listagem deve ter posição previsível em viewports estreitos (~390px), em vez de competir por linha com o grupo busca+filtros via `flex-wrap` solto.
- **Entregue**: achado revisto ao investigar a correção — `shared/components/forms/FilterBar.tsx` não tinha nenhum call site real (fundação da Sprint 8.5 nunca adotada, mesmo status de `ActionMenu`/`DeleteDialog`/`SearchInput`); `IssuesToolbar`/`ProjectsToolbar` duplicavam o mesmo layout inline. Corrigido `FilterBar` para `flex-col gap-3` → `sm:flex-row sm:items-center sm:justify-between` (mesmo idioma de `ui/dialog.tsx::DialogFooter` para o mesmo problema) **e** migrados `IssuesToolbar`/`ProjectsToolbar` para consumi-lo de fato — sem isso o fix não teria efeito visível, já que nenhuma tela importava o componente. Ver ADR-026.
- **Dependências**: 13.4 (achado que origina esta sub-sprint).
- **Critérios de aceite**: em 390px de largura, o botão de ação primária não fica espremido entre filtros; lint, type-check, testes e build verdes; verificação visual real (mesma abordagem da 13.4) antes de fechar. Confirmado em 390px/640px (fronteira `sm`)/1280px, tema claro, sem regressão em desktop.
- **DoD**: DoD-base. Última sub-sprint do escopo ampliado de M3 — **fecha o milestone**.

## M3 — Escopo ampliado: fechado (Sprint 13.1–13.5)

## M4 fase 1 — gap-analysis e quebra em sub-sprints (2026-07-19, ADR-027)

Com M3 fechado, o usuário pediu explicitamente o início do M4 — Quality. Uma auditoria de gap (agente read-only, sem edição) confirmou o estado real de cada item do escopo declarado nas ADR-020/021: Playwright, testes de componente/integração de frontend, MSW, observabilidade/métricas, revisão completa de documentação, auditoria de segurança. Achados completos e a quebra em sub-sprints estão em ADR-027. Resumo:

- **Playwright/E2E**: gap total — nenhuma config, nenhum teste, dependência não instalada.
- **MSW**: gap total — não instalado; os 15 arquivos de teste de componente existentes (~45 testes) usam só `vi.mock()` de módulo.
- **Testes de integração de frontend**: inexistentes como camada distinta da unitária, por depender de MSW.
- **Observabilidade/métricas**: log estruturado por requisição já existe (`AccessLogMiddleware`), mas sem agregação (5xx por rota, p95 por endpoint) nem endpoint `/metrics` — pendência da Sprint 9 fase 2, nunca fechada.
- **Revisão de documentação**: divergência real encontrada em `docs/04-api-design.md` §10/§11 (Notificações) — paginação documentada como cursor-based, implementação real é offset-based; endpoint `mark-all-read` e código `notification_not_found` ausentes da doc; seção ainda rotulada "pós-MVP".
- **Auditoria de segurança**: seis itens em aberto em `docs/07-security.md` (blocklist de `jti` é o mais relevante), todos já trade-offs documentados, nenhum reavaliado desde que foi aceito.
- **Gap de tooling**: `lint-staged` do frontend não roda `tsc`.

### Sprint 14.1 — M4: hardening rápido (documentação + tooling) (concluída)

- **Objetivo**: fechar os gaps de menor esforço e zero risco encontrados na auditoria antes de qualquer sub-sprint que introduza dependência nova — corrigir a divergência de documentação de notifications e adicionar `tsc` ao `lint-staged`.
- **Entregue**: `docs/04-api-design.md` §10/§11 corrigida (pagination offset-based, `mark-all-read`, `notification_not_found` documentados); `frontend/lint-staged.config.js` extraído de `package.json` com um passo `tsc -b --noEmit` adicionado à checagem de `*.{ts,tsx}`.
- **Dependências**: nenhuma — itens isolados e sem relação entre si além de ambos serem "hardening" de baixo risco.
- **Critérios de aceite**: `docs/04-api-design.md` §10/§11 batendo com `features/notifications/router.py`/`exceptions.py` real; `lint-staged` recusa commit com erro de tipo.
- **DoD**: DoD-base.

### Sprint 14.2 — M4: MSW (infraestrutura de mock de rede) (concluída)

- **Objetivo**: instalar e configurar MSW (`msw`, handlers para os endpoints já cobertos pelos testes atuais), sem ainda migrar os 15 arquivos de teste existentes.
- **Entregue**: `msw@2.15.0` instalado como devDependency; `frontend/tests/mocks/` com handlers Node (`msw/node`, `setupServer`) para os 15 endpoints já exercitados pelos 15 arquivos de teste de componente atuais (auth: login/register/logout/password-reset; projects/issues: listagem; notifications: listagem/marcar lida/marcar todas lidas; workspaces: membros/convites) organizados por feature (`handlers/auth.ts`, `handlers/projects.ts`, `handlers/issues.ts`, `handlers/notifications.ts`, `handlers/workspaces.ts`) mais fixtures compartilhadas (`fixtures.ts`); `tests/setup.ts` sobe o server global (`onUnhandledRequest: "error"`) e reseta handlers por teste. Nenhum dos 45 testes existentes migrado — todos continuam via `vi.mock()` de módulo e passam inalterados (infraestrutura inerte até a Sprint 14.3 migrar o primeiro caso).
- **Dependências**: nenhuma — fundação isolada.
- **DoD**: DoD-base.

### Sprint 14.3 — M4: testes de integração de frontend via MSW (concluída)

- **Objetivo**: migrar/expandir um subconjunto representativo dos testes de componente para exercitar via MSW em vez de `vi.mock()` de módulo, estabelecendo o padrão da camada de integração de `CLAUDE.md` §16.
- **Entregue**: 5 dos 15 arquivos de teste de componente migrados de `vi.mock()` de módulo para `server.use()`/handlers reais via MSW (`LoginForm`, `ForgotPasswordForm`, `ActiveProjectsWidget`, `RecentActivityWidget`, `WorkspaceInvitationsSettings`), cobrindo os padrões que os 10 restantes vão repetir: sucesso sem override (handler default já basta), GET com filtro por query param, GET com paginação, GET com filtragem client-side, e o caso antes não testável via `vi.mock()` — uma resposta de erro real da rede (`429`) percorrendo o interceptor de `httpClient` de verdade. As asserções que antes inspecionavam argumentos de chamada do mock (`toHaveBeenCalledWith`) viraram asserções de comportamento (o dado certo aparece porque o request certo foi feito), documentado na ADR-029. Os 10 arquivos restantes ficam para migração futura, mesmo espírito incremental do projeto — não é um requisito de bloqueio para 14.4+.
- **Dependências**: Sprint 14.2.
- **Critérios de aceite**: suíte completa (45 testes) passando após a migração; lint/type-check limpos.
- **DoD**: DoD-base.

### Sprint 14.4 — M4: Playwright (setup + fluxos críticos) (concluída)

- **Objetivo**: primeira execução real da camada E2E do projeto — setup do Playwright e os fluxos críticos já descritos em `CLAUDE.md` §16 (signup → criar workspace → criar issue → mudar status).
- **Entregue**: `@playwright/test` instalado; `frontend/playwright.config.ts` (Chromium, `webServer` reaproveitando o dev server local); `frontend/e2e/critical-flow.spec.ts` cobrindo o fluxo completo via UI real (cadastro pela aba "Criar conta" de `/login` — não havia gap de UI, achado inicial da sessão estava errado, ver ADR-030) contra um backend real. **Bug de produto real encontrado e corrigido pela primeira execução**: `EditIssueDialog` abria e fechava sozinho no primeiro clique de "Editar issue" após a issue carregar — causa raiz em `useForm({ values: {...} })` (react-hook-form) recriando o objeto de sincronização a cada render e dessincronizando o Dialog; corrigido trocando para `defaultValues` + `reset()` explícito só na transição de abertura. Detalhes completos da investigação (incluindo um beco sem saída de diagnóstico causado por um erro de configuração próprio) em ADR-030.
- **Dependências**: nenhuma obrigatória, mas executada depois de 14.2/14.3 por afinidade de assunto (infraestrutura de teste).
- **DoD**: DoD-base.

### Sprint 14.5 — M4: observabilidade e métricas backend (concluída)

- **Objetivo**: fechar a pendência da Sprint 9 fase 2 — contagem de erro 5xx por rota e latência p95 por endpoint, decidindo a abordagem técnica (endpoint `/metrics` vs. agregação sobre o log estruturado já existente) na própria sub-sprint.
- **Entregue**: `GET /metrics` (não autenticado, fora de `/api/v1`, mesmo precedente de `/health`/`/health/ready`) — decisão técnica: agregação via contadores/amostras no Redis já usado pelo rate limiting (`core/redis_client.py`, extraído de `core/rate_limit.py`), não um exportador Prometheus (mantém a exclusão de escopo já registrada na ADR-016, não a reverte). `AccessLogMiddleware` chama `core/metrics.py::record_request` reaproveitando `duration_ms`/`status_code` já calculados, agrupando por rota-template (`request.scope["route"].path`, ex. `/workspaces/{workspace_id}/issues`) — rotas não casadas (404 genuíno) caem sob um rótulo único para não crescer sem limite com sondagem externa. `p95` calculado em leitura sobre até 1000 amostras recentes por endpoint (janela móvel aproximada, sem estrutura de histograma). Detalhes completos em ADR-031.
- **Dependências**: nenhuma.
- **DoD**: DoD-base.

### Sprint 14.6 — M4: auditoria de segurança completa (concluída)

- **Objetivo**: revisão linha a linha do checklist de `docs/07-security.md`, conferência da matriz RBAC documentada contra `core/authorization.py` real, e decisão explícita sobre cada um dos seis itens em aberto (reafirmar o trade-off ou fechar) — incluindo a blocklist de `jti` em Redis.
- **Entregue**: matriz RBAC (`docs/07-security.md` §8.3) conferida permissão-por-permissão contra `core/authorization.py`/`core/permissions.py` — nenhuma divergência. Busca por bypass de `PermissionService` (checagem manual de papel fora de `core/authorization.py`) em todo `features/` — nenhum encontrado. Claims comportamentais do documento (timing attack em login, anti-enumeration de reset de senha, revogação de sessão em reuso de refresh token, checagem contextual de gerenciamento de membro, ownership override por feature) verificadas linha a linha contra o código real, não só contra a matriz estática — todas confirmadas. Dois trade-offs em aberto revisados com decisão explícita do usuário: blocklist de `jti` em Redis e access token em memória (exposição a XSS) — **ambos reafirmados**, nenhum fechado. Achado incidental de baixo risco (imprecisão de `mypy` em `core/authorization.py:55`, não um bug de runtime) registrado para pendência futura. Nenhuma mudança de código nesta sprint. Detalhes completos em ADR-032.
- **Dependências**: nenhuma — pode ser feita a qualquer momento, posicionada por último por ser a mais dependente de julgamento/decisão do usuário.
- **DoD**: DoD-base + revisão de segurança completa do checklist de `docs/07-security.md` (item de DoD da Sprint 9 nunca cumprido até aqui).

## M4 fechado (2026-07-19/20, ADR-027–032)

## M5 fase 1 — planejamento e quebra em fases (2026-07-20, ADR-033)

Com M4 fechado, o usuário pediu explicitamente o início do M5 — Kanban. Investigação prévia (agente read-only) confirmou o estado real do schema dormente: `teams`/`team_members`/`workflow_states`/`team_issue_counters` existem no banco desde a Sprint 2 (ADR-007), migrados e nunca removidos, mas sem nenhum consumidor desde a Sprint 7 (ADR-012 desacoplou `Issue` de `Team`, adotando o enum fixo de seis status atual) — `features/teams/` só tem `models.py`/`repository.py`, sem service/router/schemas, nenhuma API. A visão original (`docs/00-product-vision.md` §5, `docs/01-requirements.md` RF-TEAM-02/RF-ISSUE-05/07) pedia board **por time**, com workflow configurável por time — mas o roadmap já antecipava quebrar M5 em fases (`schema → board somente-leitura → drag-and-drop → workflow configurável por time`) em vez de entrega única.

**Decisão — Fase 1 não reativa `Team`**: apresentada a escolha entre reativar `Team`/`WorkflowState` desde já (construir Team do zero — CRUD, membership, workflow config — e devolver `team_id` a `Issue`, revertendo parte da ADR-012) ou começar mais simples — board somente-leitura, escopo de **workspace** (não de time), usando o enum de status fixo já existente, sem nenhuma mudança de schema. Escolhida a segunda opção — decisão explícita do usuário. Reativar `Team`/workflow por time fica como decisão em aberto para uma fase futura, não descartada.

### Sprint 16.1 — M5: board somente-leitura, escopo de workspace, status fixo (concluída)

- **Objetivo**: primeira tela de board do projeto — colunas pelos seis status existentes de `Issue`, escopo de workspace (mesmo escopo de `IssuesListPage` hoje), sem drag-and-drop ainda.
- **Entregue**: rota `/w/:workspaceSlug/board` (`BoardPage` → `IssuesBoardView`, `features/issues/components/`) — sem endpoint novo, reaproveita `GET /workspaces/{id}/issues` já existente (`useIssues`, `page=1&per_page=100`, mesmo limite de 100 já usado pelo padrão de "picker" do projeto — `MAX_PICKER_PAGE_SIZE`) e agrupa client-side pelos seis valores de `IssueStatus`. `IssueBoardCard` (identificador, título, prioridade, avatar do responsável) reaproveita `IssuePriorityBadge`/`workspaceRoutes.issueDetail` já existentes. `KanbanSkeleton` (`shared/components/skeletons/`, criado como placeholder não usado desde antes deste milestone) finalmente ganhou um consumidor real. Nav item "Board" na Sidebar e entrada de breadcrumb no Topbar. Consolidado `ISSUE_STATUS_LABELS` (rótulo de cada status) em `features/issues/constants.ts`, novo — havia três cópias duplicadas do mesmo mapeamento (`IssueStatusBadge`, `IssueFormFields`, `IssuesToolbar`); só a de `IssueStatusBadge` foi migrada para a nova fonte única (as outras duas continuam com sua própria cópia local, fora do escopo desta sprint — não foi um refactor geral, só evitar um quarto lugar duplicando o mesmo dado que o board precisava). Verificado visualmente (build de produção, tema claro/escuro, viewport mobile — scroll horizontal entre colunas, padrão esperado para este tipo de componente).
- **Limitação aceita**: board carrega no máximo 100 issues por workspace (mesmo limite já aceito em todo "picker" do projeto) — um workspace com mais issues que isso teria o board incompleto. Não tratado nesta fase; se necessário, a Fase 2/3 pode paginar por coluna ou usar `per_page` maior.
- **Dependências**: nenhuma.
- **DoD**: DoD-base.

### Sprint 16.2 — M5: drag-and-drop de mudança de status (concluída)

- **Objetivo**: arrastar um card entre colunas muda o status da issue (`PATCH /issues/{id}`, já existente — sem endpoint novo), com atualização otimista (RNF-PERF-03 do requisito original).
- **Entregue**: `@dnd-kit/core` (v6.3.1, aprovada explicitamente pelo usuário — ver ADR-034) integrado a `IssuesBoardView`/`IssueBoardCard`. `DndContext` com `PointerSensor` (`activationConstraint: { distance: 8 }`, resolve a ambiguidade clique-abre-detalhe vs. arrastar-muda-status sem precisar de um handle dedicado) envolve o board; cada coluna é um `useDroppable`, cada card um `useDraggable`; `DragOverlay` (portal, evita o corte pelo `overflow-x-auto` do container do board) mostra o card seguindo o ponteiro enquanto o original fica esmaecido no lugar. Nova mutação `useMoveIssueStatus` (`features/issues/hooks.ts`) — primeira do projeto com atualização otimista via `onMutate`/`setQueryData`, rollback em `onError`, reconciliação em `onSettled` — dedicada ao board (`useUpdateIssue` segue intacta para o formulário completo de edição).
- **Dependências**: Sprint 16.1. Introduziu `@dnd-kit/core` (candidata original, `react-beautiful-dnd` descontinuada) — dependência nova, aprovada explicitamente pelo usuário antes da instalação, mesma disciplina de check-in de toda dependência nova deste projeto.
- **DoD**: DoD-base. Achado incidental corrigido no mesmo escopo: `npx tsc --noEmit -p .` sozinho não checava nada neste projeto (`tsconfig.json` raiz usa `references` e `"files": []`) — comando correto é `npx tsc -b --noEmit`, agora documentado na ADR-034.

### Sprint 16.3 — M5: decisão sobre `Team`/workflow configurável por time (concluída)

- **Objetivo**: decisão explícita — reativar `Team`/`WorkflowState` (CRUD completo, membership, `team_id` de volta a `Issue`, board por time com workflow customizável) ou manter o board em escopo de workspace indefinidamente. Não decidido previamente — decisão desta própria sub-sprint, mesmo padrão da Sprint 14.5 (observabilidade) e do próprio M5 (Decisão acima).
- **Decisão**: mantido o board em escopo de workspace — `Team`/`WorkflowState` seguem como schema dormente no banco, não reativados. Nenhuma mudança de código; custo de reativar (CRUD/membership do zero, reverter parte da ADR-012, migration de schema) desproporcional ao valor incremental sem um requisito concreto pedindo workflow por time. Detalhes completos em ADR-035.
- **Dependências**: Sprint 16.1/16.2.
- **DoD**: DoD-base — satisfeita (decisão pura, sem código).

## M5 fechado (2026-07-20, ADR-033–035)

## M6 fase 1 — gap-analysis e quebra em sub-sprints (2026-07-20, ADR-036)

Com M5 fechado, o usuário pediu explicitamente o início do M6 — Production. Mesmo processo já usado para abrir M2 fase 2 (ADR-021), o escopo ampliado de M3 (ADR-024), M4 (ADR-027) e M5 (ADR-033): antes de qualquer código, uma investigação read-only confirmou o estado real de cada item do escopo declarado na visão executiva (linha 14). Achados completos em ADR-036. Resumo:

- **`MailSender`** (`backend/src/core/mail.py`): `Protocol` já existe, única implementação é `LoggingMailSender` (placeholder — nunca envia e-mail real, só loga um preview truncado do token). Ponto de extensão já documentado no próprio docstring; falta a implementação SMTP real e trocar o tipo de retorno do factory (hoje fixo em `LoggingMailSender`, não no `Protocol`).
- **`StorageProvider`** (`backend/src/core/storage.py`): mesmo padrão — só `LocalStorageProvider` (disco local, incompatível com múltiplas réplicas). O modelo de dado (`Attachment.storage_key`/`storage_provider`) já foi desenhado desde a origem para coexistência de providers (dado antigo em "local", novo em "s3", sem migração retroativa).
- **Transferência de propriedade de workspace**: gap total de endpoint/service (nenhuma rota existe), adiada desde a Sprint 4 (ADR-009) e reafirmada na Sprint 10 (ADR-018). Todos os primitivos que a feature reaproveitaria já existem: `WorkspaceService`/`WorkspaceRepositoryProtocol` (`update_member_role`, `count_members(role=...)`), `WorkspaceActivityLog` (append-only, já usado para outros eventos de membership), exceções no mesmo padrão (`CannotLeaveAsSoleOwnerError`/`CannotManageOwnerError`).
- **CI/CD**: build de imagem de produção já validado em todo PR (`push: false`), `pip-audit`/`npm audit` já rodam (não bloqueantes) — mas nenhum scan de vulnerabilidade da imagem final (Trivy/Grype) e nenhum `.env.production.example` documentando o conjunto de variáveis esperado especificamente em produção (só existe `.env.example`/`backend/.env.example` de desenvolvimento).
- **Itens que dependem de infraestrutura real** (pipeline de deploy para um orquestrador, certificado TLS, backup automatizado de banco/anexos, secret manager, autoscaling, agregação/retenção de log centralizada): nenhum é implementável dentro do repositório sem provisionar nuvem real. Opções apresentadas ao usuário — (a) documentar como decisão/runbook em ADR, mesmo critério já usado pelo `PRODUCTION_CHECKLIST.md` existente ("requer infraestrutura externa"); (b) demonstrar localmente com infraestrutura equivalente (MinIO simulando S3, TLS self-signed via Caddy, script de backup local); (c) deixar fora do M6 por completo. **Escolhida: (a)** — decisão explícita do usuário.

### Sprint 17.1 — M6: transferência de propriedade de workspace (concluída)

- **Objetivo**: endpoint + service para transferir o papel `OWNER` de um workspace para outro membro existente — orquestração atômica (rebaixar o OWNER atual, promover o alvo), reaproveitando os primitivos já existentes de `WorkspaceService`/`WorkspaceRepositoryProtocol`. UI no frontend (`WorkspaceSettingsPage`, aba Membros) para o OWNER disparar a transferência.
- **Entregue**: nova permissão `workspace.transfer_ownership` (só `OWNER`, nem `ADMIN` — mesmo padrão de `workspace.delete`); `WorkspaceService.transfer_ownership` (promove o alvo, rebaixa o ator, sincroniza `Workspace.owner_id`, registra `workspace.ownership_transferred` em `WorkspaceActivityLog`); endpoint `POST .../members/{member_id}/transfer-ownership` (idioma de ação dedicada, mesmo padrão de `.../archive`/`.../restore` de Projetos); nova exceção `CannotTransferOwnershipToSelfError` (409 `cannot_transfer_ownership_to_self`). Frontend: `useTransferOwnership` (`features/workspaces/hooks.ts`), nova prop `isOwner` propagada até `MemberRow`, ação "Transferir propriedade" via `ConfirmActionDialog`. Detalhes completos em ADR-037.
- **Dependências**: nenhuma.
- **DoD**: DoD-base satisfeita — `tsc`/`eslint`/`vitest` do frontend limpos; suíte completa do backend (`ruff`/`mypy`/`pytest`, unit+integração+contrato) rodada contra Postgres/Redis reais (ADR-042/043), **341/341 passando**. Achou e corrigiu duas regressões reais: `test_authorization.py` não previa a segunda exceção de ADMIN (ADR-042); e um bug crítico de FastAPI que quebrava o parsing de body de toda rota autenticada — `settings: Settings | None = None` bare em `get_storage_provider`/`get_mail_sender` (ADR-043), corrigido para `Depends(get_settings)`.

### Sprint 17.2 — M6: `StorageProvider` S3-compatible (concluída)

- **Objetivo**: implementação real de `StorageProvider` para um backend de objeto S3-compatible, mantendo `LocalStorageProvider` intacta (dado antigo com `storage_provider="local"` continua servível). Config nova em `Settings` (bucket, região, credenciais) via variável de ambiente.
- **Entregue**: `S3StorageProvider` (`core/storage.py`, `boto3` síncrono + `asyncio.to_thread` — aprovado explicitamente pelo usuário sobre `aioboto3`); `Settings.storage_provider` (`"local"`/`"s3"`, default `"local"`) escolhe a implementação em `get_storage_provider()`, cujo tipo de retorno foi corrigido para o `Protocol` (`StorageProvider`, não mais `LocalStorageProvider` hardcoded); `S3_BUCKET_NAME`/`S3_REGION`/`S3_ENDPOINT_URL` novos, credenciais deliberadamente fora de `Settings` (cadeia padrão do boto3). `download_attachment` (`features/attachments/router.py`) ganhou `BackgroundTask` de limpeza do arquivo temporário, condicional a `provider_name != "local"`. Serviço `minio` novo em `docker-compose.yml` (dev) e `.github/workflows/ci.yml` (via `bitnami/minio`, workaround para a limitação do bloco `services:` do GH Actions não aceitar `command:`); teste de integração (`tests/integration/test_s3_storage_provider.py`) contra MinIO real. Detalhes completos em ADR-038.
- **Dependências**: nenhuma. Introduziu dependência nova (`boto3`/`boto3-stubs[s3]`) — aprovada explicitamente pelo usuário antes de instalar, mesma disciplina já seguida para `@dnd-kit/core` (ADR-034).
- **DoD**: DoD-base satisfeita — suíte completa rodada (ADR-042/043): achou e corrigiu um `ASYNC240` real em `S3StorageProvider.open()` (cleanup síncrono dentro de método async) e o bug crítico de body-parsing descrito acima (`get_storage_provider` era uma das duas factories afetadas). `poetry.lock` regenerado corretamente com `--no-update` (só `boto3`/`boto3-stubs` + 3 transitivos triviais — a primeira tentativa, sem `--no-update`, tinha bumpado dezenas de pacotes não relacionados e foi revertida, ADR-043). Teste de integração (`tests/integration/test_s3_storage_provider.py`) escrito e sintaticamente correto, mas ainda não executado contra um MinIO real (serviço não disponível no sandbox desta sessão) — pendente validar num ambiente com Docker.

### Sprint 17.3 — M6: `MailSender` real (SMTP) (concluída)

- **Objetivo**: implementação real de `MailSender` via SMTP genérico (configurável por variável de ambiente — host/porta/credenciais/remetente), mantendo `LoggingMailSender` como fallback/dev. Corrige o tipo de retorno do factory (`Protocol`, não a implementação concreta).
- **Entregue**: `SMTPMailSender` (`core/mail.py`, `smtplib` stdlib + `asyncio.to_thread` — usuário aprovou explicitamente **não** introduzir dependência nova, sobre `aiosmtplib`); `Settings.mail_provider` (`"logging"`/`"smtp"`, default `"logging"`) escolhe a implementação em `get_mail_sender()`, retorno corrigido para o `Protocol`; `SMTP_HOST`/`SMTP_PORT`/`SMTP_USERNAME`/`SMTP_PASSWORD`/`SMTP_FROM_EMAIL`/`SMTP_USE_TLS`/`FRONTEND_BASE_URL` novos — diferente de S3, credenciais SMTP são campos de `Settings` (sem cadeia de credenciais padrão de indústria equivalente ao boto3). `docs/07-security.md` §15 atualizado explicando por que enviar o token completo por e-mail não viola o anti-enumeration. Serviço `mailhog` novo em `docker-compose.yml`/CI; teste de integração (`tests/integration/test_smtp_mail_sender.py`) contra MailHog real. Detalhes completos em ADR-039.
- **Dependências**: nenhuma. Decisão explícita do usuário de **não** introduzir dependência nova (`smtplib` stdlib sobre `aiosmtplib`) — mesma disciplina de aprovação de toda dependência nova deste projeto, aplicada aqui à escolha de não adicionar uma.
- **DoD**: DoD-base satisfeita — suíte completa rodada (ADR-042/043): `get_mail_sender` era a outra factory afetada pelo bug crítico de body-parsing corrigido na Sprint 17.1 (mesmo padrão `settings: Settings | None = None`, mesma correção). Verificação de que nenhum segredo de SMTP é logado feita por code review/docstring (`SMTPMailSender.send_password_reset` só loga `email`), não por teste automatizado (ADR-039, Desvantagens aceitas). Teste de integração (`tests/integration/test_smtp_mail_sender.py`) escrito e sintaticamente correto, mas ainda não executado contra um MailHog real (serviço não disponível no sandbox desta sessão).

### Sprint 17.4 — M6: hardening de CI (scan de imagem + template de env de produção) (concluída, verificação parcial)

- **Objetivo**: novo step no job `docker` do CI rodando Trivy ou Grype contra as imagens de produção já buildadas (não-bloqueante inicialmente, mesmo critério de `pip-audit`/`npm audit`); `.env.production.example` na raiz documentando o conjunto completo de variáveis esperadas em produção (sem valores reais, só placeholders e instrução de geração).
- **Entregue**: dois novos steps Trivy (`aquasecurity/trivy-action@0.29.0`) no job `docker`, não-bloqueantes (`continue-on-error`/`exit-code: "0"`, `severity: CRITICAL,HIGH`) — exigiu adicionar `load: true`/`tags:` aos steps de build existentes, sem os quais a imagem não fica visível ao runner. `.env.production.example` na raiz (`POSTGRES_*`, JWT, storage/mail opcionais, `VITE_API_URL`) — placeholders (`CHANGE_ME`), nunca valor real utilizável. Achado incidental corrigido no mesmo commit: `.gitignore` não cobria `.env.production` (só `.env`/`.env.local`/`.env.*.local`) — corrigido, com `!.env.production.example` para manter o template rastreado. Detalhes completos em ADR-040.
- **Dependências**: nenhuma.
- **DoD**: DoD-base parcialmente satisfeita — mesma limitação de sandbox das Sprints 17.1–17.3: sem GitHub Actions/Docker neste ambiente, os steps novos não foram executados de fato nesta sessão (YAML validado com `yaml.safe_load`). Pendente confirmar o scan Trivy rodando num push/PR real.

### Sprint 17.5 — M6: runbook/decisão para itens que exigem infraestrutura real (concluída)

- **Objetivo**: fechar `PRODUCTION_CHECKLIST.md` no nível de maturidade decidido nesta fase de planejamento — documentar em ADR a estratégia recomendada para cada item que depende de infraestrutura real (pipeline de deploy, TLS, backup, secret manager, autoscaling, agregação de log), sem código novo. Fecha M6.
- **Entregue**: `docs/11-production-runbook.md` novo — dez seções, uma por item ainda unchecked de `PRODUCTION_CHECKLIST.md`, cada uma com a estratégia real recomendada (secret manager, pipeline de deploy via GHCR, migration pré-tráfego, log centralizado, backup de Postgres/anexos, runbook de rollback, TLS na borda, autoscaling nativo) e o que já existe no código que a viabiliza. `PRODUCTION_CHECKLIST.md` ganhou uma referência cruzada por item, sem inflar sua natureza de checklist compacto. Detalhes completos em ADR-041.
- **Dependências**: Sprint 17.1–17.4 (decisão só faz sentido depois do que é código real estar fechado).
- **DoD**: DoD-base — satisfeita (decisão/documentação, sem código).

## M6 fechado (2026-07-20, ADR-036–041)

## M7 fase 1 — gap-analysis e quebra em sub-sprints (2026-07-20, ADR-044)

Com M6 fechado, o usuário importou um pacote de handoff de design pronto (`docs/design-handoff/2026-07-20-redesign-gestor/`) — protótipo navegável de alta fidelidade das 6 telas do produto sobre a marca Ring Gate já existente. Mesmo processo já usado para abrir M2–M6: antes de qualquer código, uma auditoria de gap (agente read-only) comparou o handoff tela a tela contra a implementação real. Achados completos e as decisões de sequenciamento estão em ADR-044. Resumo:

- **Risco de regressão**: Board Kanban descrito no handoff como "visão futura" — desatualizado, já shipado desde M5. Tratado como redesign de feature existente, não construção nova.
- **Fundação bloqueante**: linguagem visual nova de Status (círculo)/Prioridade (barras) consumida por 4+ telas — precisa vir antes de qualquer tela individual.
- **Gaps estruturais**: Issue detalhe (layout 3 colunas + rail editável), Projetos (grid de cards — campos ausentes do modelo de dado atual), Projeto detalhe (issues vinculadas, já no backlog "Sprint 15+").
- **Handoff modela só 5 status**, domínio real tem 6 (`IN_REVIEW`) — decisão de extensão registrada na Sprint 18.1 abaixo.
- **Falso positivo**: "bug" de foco do CommandPalette do handoff já não existe (comportamento nativo do Radix `Dialog`) — sem trabalho necessário.

### Sprint 18.1 — M7: fundação visual (tokens + glifos de Status/Prioridade) (concluída)

- **Objetivo**: tokens de cor e linguagem visual de Status/Prioridade que o handoff introduz, pré-requisito para redesenhar qualquer tela individual (4+ telas consomem `IssueStatusBadge`/`IssuePriorityBadge`).
- **Entregue**: oito tokens de cor novos (`--panel`/`--sunken`/`--t2`/`--t3`/`--border2`/`--redbg`/`--amber`/`--green`, `:root`+`.dark` em `index.css`, valores literais do handoff — `--bg`/`--text`/`--red` do handoff mapeiam para `--background`/`--foreground`/`--destructive` já existentes, não duplicados); `IssueStatusIcon`/`IssuePriorityIcon` novos (`features/issues/components/`, glifo via CSS inline — círculo com `conic-gradient` parcial para status, "barras de equalizador" para prioridade) substituindo a pílula `Badge`/ícones lucide anteriores; `IssueStatusBadge`/`IssuePriorityBadge` recompostos sobre os novos ícones sem alterar a assinatura de props, os 4 call sites existentes (`IssuesTable`, `IssueDetailView`, `MyIssuesWidget`, `IssueBoardCard`) inalterados. `IN_REVIEW` (6º status, ausente do handoff que só modela 5) resolvido reaproveitando `--amber` com fatia maior do `conic-gradient` (270° vs. 180° de "Em andamento") em vez de inventar uma cor nova. Documentado em `design-system/colors.md`/`badges.md`. Detalhes completos em ADR-044.
- **Dependências**: nenhuma — primeira sub-sprint do milestone.
- **DoD**: DoD-base.

### Sprint 18.2 — M7: redesign visual do Board Kanban (concluída)

- **Objetivo**: redesenhar cartão/coluna do Board Kanban (já em produção desde M5) consumindo a fundação visual da Sprint 18.1, sem tocar a lógica de drag-and-drop.
- **Entregue**: `IssueBoardCard`/`IssueBoardCardPreview` recompostos (fundo `--panel`, borda `--border`/hover `--border2`, sombra one-off do handoff, layout em 3 linhas — id+prioridade, título, avatar); `IssuesBoardView` com ícone de status no cabeçalho de coluna, destaque de drag-over em `--sunken`/`--border2`, placeholder de coluna vazia com borda tracejada, e título+subtítulo da página (inexistentes antes, inconsistente com `IssuesListPage`); `useMoveIssueStatus` ganha `onSuccess` com toast de confirmação (`"{identifier} → {label}"`), gap identificado na auditoria de M7. Chip de label no cartão **não implementado** — `IssueResponse` não inclui labels na listagem, mudança de contrato fora do escopo desta sub-sprint visual. Toggle Lista/Board e botão "Nova issue" no header do board também não implementados — redundantes com a Sidebar. Detalhes completos em ADR-045.
- **Dependências**: Sprint 18.1 (consome os tokens/ícones novos).
- **DoD**: DoD-base.

### Sprint 18.3 — M7: Issue detalhe — layout 3 colunas + rail editável inline (concluída)

- **Objetivo**: maior gap estrutural de M7 — trocar a coluna única com metadados só-leitura (`<dl>`) por um layout de 3 colunas (conteúdo + rail lateral), com Status/Prioridade/Responsável/Projeto/Estimativa/Vencimento editáveis direto no rail via dropdown, sem abrir o modal de edição completo.
- **Entregue**: `IssueDetailView` reescrito (link "← Issues", título em `font-heading`, seções Anexos/Atividade/Comentários com heading uppercase e reordenadas para bater com o handoff); `IssueDetailRail.tsx` novo — 6 campos editáveis inline via `DropdownMenu` (item = mutação imediata via `useUpdateIssue`, já existente — nenhuma mutação nova), reaproveitando `IssueStatusIcon`/`IssuePriorityIcon` (18.1) e o estilo de avatar do board card (18.2); `IssueLabelPicker` (Sprint 8) só realocado para o rail, não reescrito; `IssueActivityTimeline` restilizado (ponto + nome + hora). Vencimento no rail só oferece atalhos relativos (Amanhã/1 semana/2 semanas), data arbitrária continua no `EditIssueDialog`. Descrição continua texto plano — blocos rich-text do handoff exigiriam mudança de schema, fora de escopo. Detalhes completos em ADR-046.
- **Dependências**: Sprint 18.1/18.2 (reaproveita ícones e padrão de avatar).
- **DoD**: DoD-base.

### Sprint 18.4 — M7: redesign visual da listagem de Issues (concluída)

- **Objetivo**: fechar o redesign de `Inicio e Issues.dc.html` na parte de listagem — cabeçalho com contagem total, ícones de status/prioridade consistentes com Board (18.2)/Detalhe (18.3) em vez das badges com texto da Sprint 18.1, tempo relativo de atualização (requisito do handoff, README §3 "tempo relativo").
- **Entregue**: `IssuesTable` com `IssueStatusIcon`/`IssuePriorityIcon` isolados (envolvidos em `role="img"`/`aria-label`/`title` para não perder o rótulo textual perdido ao tirar a badge) substituindo `IssueStatusBadge`/`IssuePriorityBadge`, e coluna nova "Atualizado" (`formatRelativeTime`, novo em `shared/lib/date.ts`); `IssuesListPage` com `<h1>` em `font-heading` + contagem total (`{meta.total} issues`) e o botão "Nova issue" migrado da toolbar para o cabeçalho, ao lado do título (antes dentro de `IssuesToolbar`/`FilterBar`, como no handoff); `ISSUE_PRIORITY_LABELS` extraído para `constants.ts` (era a 4ª cópia local do mesmo mapa — `IssuePriorityBadge`, `IssueDetailRail`, `IssuesTable` — cruzando o limiar que a própria ADR-046 previa). Toggle Lista/Board e filtros multi-seleção com contador do handoff **não implementados** — mesma decisão já tomada no Board (ADR-045, redundante com a Sidebar) e mesma limitação de contrato já aceita (`IssueListParams` só aceita um `status`/`priority` por vez, não lista) — os `Select` existentes de `IssuesToolbar` foram mantidos.
- **Achado durante a sprint**: a suíte Playwright (`e2e/critical-flow.spec.ts`) já estava quebrada pelas mudanças não commitadas da Sprint 18.3 — a asserção final checava um `[data-slot="badge"]` com "In Progress" na página de detalhe, mas `IssueDetailRail` (18.3) substituiu a badge por um botão de dropdown sem esse marcador. Corrigido para checar o texto visível "In Progress" diretamente (mesmo padrão já usado mais acima no próprio teste, linha do "Backlog").
- **Dependências**: Sprint 18.1/18.2/18.3 (reaproveita ícones e constantes).
- **DoD**: DoD-base.

### Sprint 18.5 — M7: redesign do Início/Dashboard (concluída)

- **Objetivo**: fechar o redesign de `Inicio e Issues.dc.html` na tela de Início — saudação dinâmica por horário, data por extenso e resumo textual do radar do usuário (inexistentes antes: cabeçalho era só "Olá, {nome}" estático), três widgets restilizados com a linguagem visual do handoff.
- **Entregue**: `shared/lib/date.ts` ganha `getGreeting`/`formatLongDate`/`formatRelativeTime` (mesma lógica de `data.js::saudacao`/`hojeLongo`/`timeAgo` do handoff); `features/dashboard/hooks.ts` novo — `useMyRadarIssues` (issues atribuídas ao usuário, status `BACKLOG`/`TODO`/`IN_PROGRESS`, ordenadas por prioridade, limitadas a 6 — mesma fonte usada pelo widget "Minhas issues" e pelo resumo do cabeçalho, filtro por múltiplos status feito client-side sobre uma página maior porque `IssueListParams` só aceita um `status`); `DashboardWidgetCard.tsx` novo (casca `--panel`/`--border`/cabeçalho uppercase reaproveitada pelos 3 widgets, substituindo o `Card` shadcn genérico — mesma decisão de estilização própria de `IssueBoardCard`/`IssueDetailRail`); `MyIssuesWidget` (linhas com ícone de prioridade+status, id, título, vencimento), `ActiveProjectsWidget` (nome+descrição, data-alvo, avatar do líder via `useWorkspaceMembers`) e `RecentActivityWidget` (avatar+nome em negrito+verbo+identificador da issue+tempo relativo, sobre a mesma fonte de notificações já existente) restilizados sobre `DashboardWidgetCard`. `workspaceName` removido de `DashboardView`/`DashboardPage` — ficou sem uso (breadcrumb do Topbar já mostra o nome do workspace).
- **Não implementado (decisão explícita, mesmo padrão de deferimento de ADR-045/046)**: barra de progresso por projeto (issues concluídas/total) do handoff — `ProjectResponse` não expõe contagem de issues por projeto, mudança de contrato fora do escopo de uma sub-sprint visual; feed de "Atividade recente" continua sobre notificações pessoais (Sprint 10/M2), não um feed de atividade do workspace inteiro — nenhuma API de atividade global existe hoje, e essa distinção já era assim antes desta sub-sprint.
- **Dependências**: Sprint 18.1/18.2 (ícones/avatar), Sprint 18.4 (`useMyRadarIssues` reaproveita o mesmo `useIssues`).
- **DoD**: DoD-base — `tsc -b --noEmit`, `eslint`, `vitest` (17 arquivos, 49/49) e `npm run build` limpos; testes de `MyIssuesWidget`/`ActiveProjectsWidget`/`RecentActivityWidget` atualizados para a nova cópia de texto (empty state "Nada atribuído a você").

`Inicio e Issues.dc.html` (Sprints 18.1–18.5) está com todas as 5 telas do arquivo endereçadas (Board marcado como "visão futura" pelo handoff já era feature real desde M5, redesenhado na 18.2). As próximas telas do pacote de handoff (`Projetos e Labels.dc.html`, `Administracao.dc.html`, `Autenticacao.dc.html`, `Sidebar`/`NotifBell`/`CommandPalette`) ficam para as próximas sub-sprints de M7 — Projetos exige decisão de schema antes do visual (grid de cards pede campos que `Project` não tem, ver ADR-044).

## M7 fase 2 — gap-analysis e quebra em sub-sprints (Projetos e Labels) (2026-07-21, ADR-049)

Fechada a fase 1 (`Inicio e Issues.dc.html`), a próxima tela do handoff é `Projetos e Labels.dc.html` (+ `data.js`/`README.md` §7–9). Mesmo processo das fases anteriores: antes de qualquer código, uma auditoria de gap (agente read-only) comparou o handoff contra as features reais `Project`/`Label`. Ao contrário de M7 fase 1 (quase toda visual), aqui o gap é **estrutural** — o grid de cards e a tela de labels dependem de dados que o modelo não expõe, exatamente a pendência que ADR-044/ADR-048 já haviam registrado como bloqueante. Achados completos em ADR-049. Resumo:

- **Key de projeto**: card exibe uma sigla curta ("ONB", "PAL") que `Project` não tinha — decorativa, sem relação com o `FD-{n}` de Issue.
- **Membros de projeto**: cards mostram avatares de membros — não existia associação usuário↔projeto (só `lead_id`, um único líder).
- **Progresso/uso**: cards mostram issues concluídas/total; a tela de labels mostra nº de issues por label — nenhuma contagem existia, e calcular client-side seria N+1 (razão pela qual a barra de progresso do dashboard foi adiada na ADR-048).

A fase foi quebrada em três sub-sprints: 19.1 (schema/backend, esta) destrava 19.2 (grid de cards de Projetos) e 19.3 (tela de Labels), ambas de UI.

### Sprint 19.1 — M7: schema de Projetos/Labels (`Project.key`, `ProjectMember`, agregações de progresso/uso) (concluída, verificação parcial)

- **Objetivo**: fundação backend/schema da fase 2 de M7 — os três campos ausentes que o grid de cards e a tela de labels do handoff exigem, sem tocar frontend. Backend-only por design, para destravar 19.2/19.3.
- **Entregue**: `Project.key` (2–4 letras maiúsculas, opcional na criação/auto-derivada do nome via `core/project_key.py`, validada, única por workspace via índice parcial `uq_projects_workspace_id_key_active` — cópia do padrão de `slug`; decorativa, sem relação com `FD-{n}`); `ProjectMember` (tabela nova — associação **informativa** usuário↔projeto, **não** controle de acesso: RBAC de projeto está fora de escopo, o RBAC de workspace continua a única camada de autorização; `add_member` idempotente, endpoints `POST/DELETE .../projects/{id}/members` gated pela mesma `Permission.PROJECT_UPDATE` do `PATCH`, com validação de que o alvo já é membro do workspace); `ProjectResponse` ganha `member_ids`/`issue_count`/`done_issue_count` e `LabelResponse` ganha `issue_count`, todos via **uma agregação por página** (nunca N+1) — o service passa a devolver DTOs (`ProjectView`/`LabelView`) e o router monta a resposta via `from_view`. Duas migrações separadas e reversíveis. Detalhes completos em ADR-049.
- **Dependências**: nenhuma no frontend; assenta sobre as features `Project` (Sprint 6) e `Label` (Sprint 8) e o RBAC de workspace (Sprint 5).
- **DoD**: DoD-base parcial — `ruff`/`mypy` limpos nos arquivos tocados, `pytest tests/unit` verde (179); testes de integração/contrato escritos mas **não executados contra Postgres real** neste ambiente (sandbox sem Postgres/Redis, mesma limitação das Sprints 17.x) — rodam em CI com `alembic upgrade head`.

## Sprint 15+ — Extensões futuras (pós-portfólio)

Não planejadas em detalhe agora (evita over-engineering especulativo, `CLAUDE.md` §1.6); candidatas registradas para não serem esquecidas: integrações externas (GitHub, Slack), colaboração em tempo real via WebSocket, papel `GUEST` completo, anexos de arquivo em UI (schema de `Attachment` já existe desde a Sprint 2, falta a feature), refinamento avançado da command palette (ex.: paginação de resultados, busca por label), página dedicada de notificações (hoje o popover do Topbar trunca nas 10 mais recentes, achado na auditoria de M2 fase 2 mas fora do escopo redefinido do milestone), app mobile, `ProjectDetailPage` listar/filtrar as issues do próprio projeto (achado (b) da Sprint 13.4 — `Issue.project_id` já existe no schema, falta a UI), migrar `LabelsToolbar`/demais toolbars futuras para `SearchInput` (`shared/components/forms/SearchInput.tsx`, fundação da Sprint 8.5 ainda sem call site — fora do escopo da Sprint 13.5, que só corrigiu o reflow, não substituiu o markup de busca). Command palette em sua forma funcional básica deixou de estar nesta lista — entregue na Sprint 10/M2. Playwright/regressão visual automatizada (M4, ver ressalva da Sprint 11 acima) também deixa de ser "futuro distante" para virar candidato concreto do próximo milestone.
