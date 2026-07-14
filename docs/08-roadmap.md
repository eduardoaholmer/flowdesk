# 08 — Roadmap

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

## Sprint 7 — Colaboração

- **Objetivo**: recursos que dependem do núcleo de issues já existir, sobre o schema de `Comment`/`ActivityLog` da Sprint 2.
- **Funcionalidades**: RF-COMMENT-01 a 03; RF-ISSUE-10 (atividade).
- **Dependências**: Sprint 6.
- **Critérios de aceite**: comentários com CRUD e permissões corretas; menção `@usuário` reconhecida e armazenada; log de atividade completo e visível no detalhe da issue, cobrindo ao menos criação, mudança de status, mudança de responsável.
- **DoD**: DoD-base.

## Sprint 8 — Planejamento (Ciclos)

> **Nota (pós-execução da Sprint 6)**: RF-PROJ-01 (feature de Projetos) já foi entregue na Sprint 6, adiantada em relação a este planejamento original — ver nota na Sprint 6 e ADR-011. Esta sprint mantém em aberto só o que Projetos-a-feature não cobriu: `Cycle` (ainda não modelado) e o join `Project ↔ Team`.
- **Objetivo**: camada de planejamento acima da issue individual — modelar `Cycle` (ainda não existe) e o join `Project ↔ Team`, e agrupar issues em ciclos com cálculo de progresso.
- **Funcionalidades**: RF-CYCLE-01, 02.
- **Dependências**: Sprint 6 (issues precisam existir para serem agrupadas; a feature de Projetos já está pronta desde a Sprint 6).
- **Critérios de aceite**: projeto agrupando issues de múltiplos times (via o novo join `Project ↔ Team`); ciclo com cálculo de progresso (burndown simples) correto contra dados de teste conhecidos.
- **DoD**: DoD-base.

## Sprint 9 — Polimento e Observabilidade

- **Objetivo**: fechar lacunas de produção real antes de considerar o MVP+ "apresentável". `Notification` já está modelada desde a Sprint 2.
- **Funcionalidades**: RF-NOTIF-01, 02; RF-AUTH-06 (recuperação de senha); hardening de rate limit por rota; métricas básicas (contagem de erro 5xx por rota, latência p95 por endpoint).
- **Dependências**: Sprints 3–8.
- **Critérios de aceite**: notificação in-app gerada e visível para menção e mudança de status; reset de senha funcional; dashboard mínimo (ainda que só via logs estruturados agregáveis) mostrando latência e taxa de erro por rota.
- **DoD**: DoD-base + revisão de segurança completa do checklist de `docs/07-security.md`.

## Sprint 10+ — Extensões futuras (pós-portfólio)

Não planejadas em detalhe agora (evita over-engineering especulativo, `CLAUDE.md` §1.6); candidatas registradas para não serem esquecidas: integrações externas (GitHub, Slack), colaboração em tempo real via WebSocket, papel `GUEST` completo, anexos de arquivo em UI (schema de `Attachment` já existe desde a Sprint 2, falta a feature), command palette avançado, app mobile.
