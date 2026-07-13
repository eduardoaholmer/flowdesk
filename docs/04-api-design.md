# 04 — Design da API

## 1. Convenções gerais

- **Base URL**: `/api/v1`. Versionamento vai no path (não em header) para ser visível e cacheável trivialmente — mudança incompatível de contrato nasce como `/api/v2`, o contrato anterior continua servido até deprecação formal.
- **Formato**: JSON em request e response (`Content-Type: application/json`). Datas em ISO 8601 UTC (`2026-07-13T14:30:00Z`). IDs em UUID string.
- **Envelope de resposta**: ver `CLAUDE.md` §8 (`{ data }`, `{ data, meta }` para coleções, `{ error }` para falhas).
- **Autenticação**: header `Authorization: Bearer <access_token>` em toda rota exceto `POST /auth/register`, `POST /auth/login`, `POST /auth/refresh`. Refresh token trafega apenas via cookie `HttpOnly`.
- **Autorização**: declarada por rota na tabela de cada recurso abaixo, resolvida via `Depends(require_permission(...))` (`CLAUDE.md` §10). Papéis: `OWNER > ADMIN > MEMBER > GUEST` (matriz completa em `docs/07-security.md`).
- **Paginação**: cursor-based para coleções de alto volume (`issues`, `activity_logs`, `notifications`) — `?cursor=<opaque>&limit=50` (default `limit=20`, máx `100`); offset-based (`?page=1&per_page=20`) para coleções pequenas e estáveis (`members`, `teams`, `labels`) onde "ir para a página 5" é uma interação real de UI. Justificativa em ADR (ver `docs/09-decision-log.md`, nota em ADR-002): cursor evita o problema de paginação instável quando novas issues são inseridas entre páginas; offset é aceitável quando o volume é pequeno o suficiente para nunca importar.
- **Filtros**: query params nomeados por campo (`?status=in_progress&assignee_id=<uuid>&label=bug`), combináveis com AND. Múltiplos valores do mesmo campo = OR dentro do campo (`?status=todo&status=in_progress`).
- **Ordenação**: `?sort=-updated_at` (prefixo `-` = descendente). Campo default documentado por recurso.
- **Idempotência**: `POST` de criação aceita header opcional `Idempotency-Key`; requisições repetidas com a mesma chave dentro de 24h retornam a resposta original em vez de duplicar o recurso (mitigação de duplo-clique/retry de rede).
- **Concorrência otimista**: recursos versionados (`issues`) exigem `If-Match: <version>` em `PATCH`; divergência retorna `409 Conflict` (`code: "version_conflict"`).

### Códigos HTTP usados

| Código | Uso |
|---|---|
| 200 | Sucesso em leitura ou atualização |
| 201 | Criação de recurso (corpo contém o recurso criado) |
| 204 | Sucesso sem corpo (ex.: `DELETE`) |
| 400 | Requisição malformada (JSON inválido) |
| 401 | Não autenticado / token inválido ou expirado |
| 403 | Autenticado, mas sem permissão para a ação |
| 404 | Recurso não encontrado (ou existe, mas fora do workspace do usuário — nunca vazamos a distinção) |
| 409 | Conflito (duplicidade, versão otimista divergente, transição de estado inválida) |
| 422 | Corpo válido como JSON, mas falha de validação de schema |
| 429 | Rate limit excedido |
| 500 | Erro não tratado (logado, nunca detalhado ao cliente) |

## 2. Autenticação (`/auth`)

| Ação | Endpoint | Auth | Request | Response | Códigos |
|---|---|---|---|---|---|
| Registrar | `POST /auth/register` | Nenhuma | `{ name, email, password }` | `{ data: { user } }` | 201, 409 (`email_already_registered`), 422 |
| Login | `POST /auth/login` | Nenhuma | `{ email, password }` | `{ data: { access_token, user } }` + cookie `refresh_token` | 200, 401 (`invalid_credentials`), 429 |
| Refresh | `POST /auth/refresh` | Cookie `refresh_token` + header CSRF | — | `{ data: { access_token } }` + rotaciona cookie | 200, 401 (`invalid_refresh_token`) |
| Logout | `POST /auth/logout` | Bearer | — | 204, limpa cookie, revoga token no banco | 204, 401 |
| Usuário atual | `GET /auth/me` | Bearer | — | `{ data: { user, workspaces: [...] } }` | 200, 401 |

Regras de negócio notáveis: `register` não realiza login automático (fluxo explícito, evita ambiguidade de estado); `refresh` fora do padrão (detecção de reuso de refresh token revogado) está detalhado em `docs/07-security.md`.

## 3. Workspaces (`/workspaces`)

| Ação | Endpoint | Autorização | Request | Response | Códigos |
|---|---|---|---|---|---|
| Criar | `POST /workspaces` | Qualquer usuário autenticado | `{ name, slug }` | `{ data: { workspace } }`, criador vira `OWNER` | 201, 409 (`slug_taken`), 422 |
| Listar minhas | `GET /workspaces` | Autenticado | — | `{ data: [workspace] }` | 200 |
| Detalhe | `GET /workspaces/{workspace_id}` | Membro do workspace | — | `{ data: { workspace } }` | 200, 403, 404 |
| Atualizar | `PATCH /workspaces/{workspace_id}` | `OWNER` | `{ name?, slug? }` | `{ data: { workspace } }` | 200, 403, 409 (`slug_taken`) |
| Excluir | `DELETE /workspaces/{workspace_id}` | `OWNER` | — | 204 (soft delete) | 204, 403 |

### Membros (`/workspaces/{workspace_id}/members`)

| Ação | Endpoint | Autorização | Request | Response | Códigos |
|---|---|---|---|---|---|
| Listar | `GET .../members?page=&per_page=&role=` | Membro | — | `{ data: [member], meta }` | 200 |
| Convidar | `POST .../invitations` | `OWNER`/`ADMIN` | `{ email, role }` | `{ data: { invitation } }` | 201, 403, 409 (`already_member`) |
| Aceitar convite | `POST /invitations/{token}/accept` | Autenticado (e-mail deve bater) | — | `{ data: { workspace_member } }` | 200, 400 (`invitation_expired`), 403 |
| Alterar papel | `PATCH .../members/{member_id}` | `OWNER`/`ADMIN` (não pode alterar `OWNER`) | `{ role }` | `{ data: { member } }` | 200, 403, 422 |
| Remover | `DELETE .../members/{member_id}` | `OWNER`/`ADMIN` | — | 204 | 204, 403 (não pode remover `OWNER`) |

## 4. Times (`/workspaces/{workspace_id}/teams`)

| Ação | Endpoint | Autorização | Request | Response | Códigos |
|---|---|---|---|---|---|
| Criar | `POST .../teams` | `ADMIN`+ | `{ name, key }` | `{ data: { team } }` (cria workflow default) | 201, 409 (`key_taken`), 422 |
| Listar | `GET .../teams` | Membro | — | `{ data: [team], meta }` | 200 |
| Detalhe | `GET .../teams/{team_id}` | Membro do time ou `ADMIN`+ | — | `{ data: { team, workflow_states } }` | 200, 403, 404 |
| Atualizar | `PATCH .../teams/{team_id}` | `ADMIN`+ | `{ name? }` | `{ data: { team } }` | 200, 403 |
| Excluir | `DELETE .../teams/{team_id}` | `ADMIN`+ | — | 204 | 204, 403 |
| Adicionar membro | `POST .../teams/{team_id}/members` | `ADMIN`+ | `{ user_id }` | `{ data: { team_member } }` | 201, 403, 409 |
| Remover membro | `DELETE .../teams/{team_id}/members/{user_id}` | `ADMIN`+ | — | 204 | 204, 403 |
| Configurar workflow | `PUT .../teams/{team_id}/workflow-states` | `ADMIN`+ | `{ states: [{ name, category, position }] }` | `{ data: { workflow_states } }` | 200, 409 (`states_in_use`, se remoção afeta issue existente) |

## 5. Issues (`/workspaces/{workspace_id}/issues`)

| Ação | Endpoint | Autorização | Request | Response | Códigos |
|---|---|---|---|---|---|
| Criar | `POST .../issues` | Membro do time | `{ team_id, title, description?, status_id?, priority?, assignee_id?, label_ids?, project_id?, cycle_id? }` | `{ data: { issue } }` (gera `number` sequencial) | 201, 403, 404 (`team_not_found`), 422 |
| Listar/Board | `GET .../issues?team_id=&status=&assignee_id=&label=&priority=&q=&sort=&cursor=&limit=` | Membro do time | — | `{ data: [issue], meta: { next_cursor } }` | 200, 403 |
| Detalhe | `GET .../issues/{issue_id}` | Membro do time da issue | — | `{ data: { issue, labels, comments_count } }` | 200, 403, 404 |
| Atualizar | `PATCH .../issues/{issue_id}` | Membro do time (ver matriz §RBAC) | `{ title?, description?, status_id?, priority?, assignee_id?, label_ids? }` + header `If-Match` | `{ data: { issue } }` | 200, 403, 404, 409 (`version_conflict` ou `invalid_status_transition`) |
| Excluir | `DELETE .../issues/{issue_id}` | Criador ou `ADMIN`+ | — | 204 (soft delete) | 204, 403, 404 |
| Atividade | `GET .../issues/{issue_id}/activity` | Membro do time | — | `{ data: [activity_log], meta: { next_cursor } }` | 200 |

`q` no filtro de listagem aciona busca textual (índice GIN, §9 de `docs/03-database.md`); demais filtros combinam via AND. Ordenação default: `-updated_at`.

## 6. Comentários (`/workspaces/{workspace_id}/issues/{issue_id}/comments`)

| Ação | Endpoint | Autorização | Request | Response | Códigos |
|---|---|---|---|---|---|
| Criar | `POST .../comments` | Membro do time | `{ body }` | `{ data: { comment } }` | 201, 403, 404 |
| Listar | `GET .../comments?cursor=&limit=` | Membro do time | — | `{ data: [comment], meta }` | 200 |
| Atualizar | `PATCH .../comments/{comment_id}` | Autor | `{ body }` | `{ data: { comment } }` | 200, 403 |
| Excluir | `DELETE .../comments/{comment_id}` | Autor ou `ADMIN`+ | — | 204 | 204, 403 |

## 7. Labels (`/workspaces/{workspace_id}/labels`)

| Ação | Endpoint | Autorização | Request | Response | Códigos |
|---|---|---|---|---|---|
| Criar | `POST .../labels` | `MEMBER`+ | `{ name, color }` | `{ data: { label } }` | 201, 409 (`name_taken`) |
| Listar | `GET .../labels` | Membro | — | `{ data: [label], meta }` | 200 |
| Atualizar | `PATCH .../labels/{label_id}` | `ADMIN`+ | `{ name?, color? }` | `{ data: { label } }` | 200, 403 |
| Excluir | `DELETE .../labels/{label_id}` | `ADMIN`+ | — | 204 (desvincula de issues) | 204, 403 |

## 8. Projetos e Ciclos — pós-MVP (`/workspaces/{workspace_id}/projects`, `/teams/{team_id}/cycles`)

Contrato análogo ao de Times/Issues (CRUD + listagem paginada + autorização por papel); detalhado no início da sprint correspondente em `docs/08-roadmap.md`, não especificado em profundidade agora para não travar a Sprint 0 em contrato de features fora do MVP — evita retrabalho caso o modelo mude durante a implementação do núcleo.

## 9. Notificações — pós-MVP (`/notifications`)

| Ação | Endpoint | Autorização | Response | Códigos |
|---|---|---|---|---|
| Listar | `GET /notifications?read=&cursor=&limit=` | Dono do recurso (usuário autenticado, implícito) | `{ data: [notification], meta }` | 200 |
| Marcar como lida | `PATCH /notifications/{id}` | Dono do recurso | `{ data: { notification } }` | 200, 403 |

## 10. Erros — catálogo de `code` (não exaustivo, cresce por feature)

`invalid_credentials`, `email_already_registered`, `invalid_refresh_token`, `slug_taken`, `key_taken`, `name_taken`, `already_member`, `invitation_expired`, `team_not_found`, `issue_not_found`, `version_conflict`, `invalid_status_transition`, `permission_denied`, `rate_limited`, `validation_error`.

Todo novo `code` introduzido em uma feature deve ser adicionado a este catálogo no mesmo PR (regra também em `CLAUDE.md` §17).
