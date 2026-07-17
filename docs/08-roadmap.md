# 08 — Roadmap

## Milestones (visão executiva, pós-auditoria 2026-07-16)

A partir da conclusão do Milestone 1, o roadmap passa a ser acompanhado em dois níveis: **Milestone** (agrupamento executivo de várias sprints em torno de um objetivo de produto) e **Sprint** (unidade de execução, detalhada seção a seção abaixo). Esta camada não substitui as sprints já registradas — apenas as agrupa retroativamente e ordena o que vem a seguir. A ordem abaixo é uma decisão explícita do usuário que **inverte a prioridade original** de `docs/00-product-vision.md` (que tratava board/Kanban como MVP): o Kanban deixou de ser considerado MVP e passa a ser um milestone grande por si só, só depois de uma base de produto completa e polida.

> **Nota (pós-auditoria de gap, ADR-021)**: o Kanban **não foi removido do produto** — só deixou de fazer parte do MVP/corte inicial. `M5 — Kanban` continua no roadmap como uma feature "premium" construída sobre uma base de produto e de engenharia madura, não descartada. Nenhum trabalho de Kanban começa antes de M4 estar concluído.

- ✅ **M1 — Estabilização** (concluído): Sprints 0–9 fase 1. Notificações, recuperação de senha, hardening de rate limit e estabilização da suíte de testes (ADR-017).
- 🔄 **M2 — Product Completeness** (em andamento, fase 2): transformar o FlowDesk em um produto realmente utilizável antes do Kanban. Fase 1 (Sprint 10, ADR-018) entregou administração de workspace, command palette e a decisão do dashboard (removido). Fase 2 (Sprints 12.1–12.4, ADR-021), aberta após uma auditoria de gap de 2026-07-16, cobre o que a fase 1 não tocou: correção de UX e revisão de navegação — ver detalhamento abaixo.
- ✅ **M3 — Ring Gate Brand** (concluído fase 1, escopo ampliado pendente): Sprint 11 (ADR-019) entregou a rampa de cor semântica e o motion system CSS-only. O usuário ampliou o escopo do milestone para incluir tipografia, app icon, microinterações e uma revisão visual completa de todo componente — esse escopo ampliado só será detalhado/planejado quando M2 fechar (mesma disciplina de "não pular etapas" usada para M2), não nesta ADR.
- **M4 — Quality**: Playwright, testes de componente, testes de integração de frontend, MSW, observabilidade, métricas, revisão completa de documentação, auditoria de segurança. Ver ADR-020/ADR-021 para o detalhamento de escopo herdado da versão anterior deste milestone ("Engineering Quality").
- **M5 — Kanban**: `Team`/`WorkflowState` (schema dormente desde a Sprint 2/ADR-007, nunca removido) mais board com drag-and-drop — o antigo "Núcleo de Issues" original da Sprint 0/4/6 nunca executado nessa forma. Deixou de ser considerado feature inicial de produto (`docs/00-product-vision.md` §5 original) — é agora uma feature premium construída só depois que o sistema inteiro estiver sólido (M2–M4 fechados). Ao chegar neste milestone, o trabalho será quebrado em múltiplas fases de implementação (schema → board read-only → drag-and-drop → workflow configurável por time, por exemplo) em vez de uma entrega única. **Não implementar nada relacionado a Kanban antes da conclusão de M4.**
- **M6 — Production**: deploy real, backups, TLS, secrets, CI/CD, infraestrutura, escalabilidade — inclui `MailSender`/`StorageProvider` com implementação real (hoje só `LoggingMailSender`/`LocalStorageProvider`) e transferência de propriedade de workspace (nunca implementada, ver ADR-009/ADR-018).

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

### Sprint 12.4 — M2: polimento do command palette (planejada)

- **Objetivo**: fechar os gaps de UX assíncrona do command palette encontrados na auditoria.
- **Escopo previsto**: indicador de carregamento durante a busca de issues/projetos (hoje pode ler como busca morta entre o debounce e a resposta); estado de erro/retry quando a busca falha (hoje falha silenciosamente como "nenhum resultado").
- **Dependências**: nenhuma — componente isolado (`shared/components/command-palette/`).
- **DoD**: DoD-base + aprovação explícita do usuário antes de fechar M2 fase 2 e considerar o escopo ampliado de M3 (tipografia/app icon/microinterações/revisão visual completa).

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
- **DoD**: DoD-base. Mesma ressalva de verificação visual em navegador real da Sprint 12.5 (Docker inacessível neste sandbox) — recomendado ao usuário validar via `docker compose up`/`npm run dev` antes de considerar M2 fase 2 pronta para revisão final (12.2–12.4 seguem pendentes).

## Sprint 13+ — Extensões futuras (pós-portfólio)

Não planejadas em detalhe agora (evita over-engineering especulativo, `CLAUDE.md` §1.6); candidatas registradas para não serem esquecidas: integrações externas (GitHub, Slack), colaboração em tempo real via WebSocket, papel `GUEST` completo, anexos de arquivo em UI (schema de `Attachment` já existe desde a Sprint 2, falta a feature), refinamento avançado da command palette (ex.: paginação de resultados, busca por label), página dedicada de notificações (hoje o popover do Topbar trunca nas 10 mais recentes, achado na auditoria de M2 fase 2 mas fora do escopo redefinido do milestone), app mobile. Command palette em sua forma funcional básica deixou de estar nesta lista — entregue na Sprint 10/M2. Playwright/regressão visual automatizada (M4, ver ressalva da Sprint 11 acima) também deixa de ser "futuro distante" para virar candidato concreto do próximo milestone.
