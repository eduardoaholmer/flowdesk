# 06 — Backend

Stack: Python 3.12, FastAPI, SQLAlchemy 2.0 (async), Alembic, Pydantic v2, PostgreSQL, Redis, Poetry, Pytest. Este documento detalha a organização interna; o fluxo de camadas normativo está em `CLAUDE.md` §3–§11 — aqui aprofundamos *como* cada peça é implementada.

## 1. Organização dos Services

- Um `Service` por agregado de domínio, instanciado por requisição via DI (nunca singleton com estado mutável entre requisições).
- Assinatura típica de método: recebe `workspace_id`, o `CurrentUser` (autenticado, já resolvido pela camada de DI) e um DTO de entrada; retorna a entidade de domínio (model ORM) ou uma dataclass de resultado.
- Services não têm conhecimento de `Request`/`Response` do FastAPI nem de status HTTP — o mapeamento para HTTP é responsabilidade do router + exception handler global. Isso é o que permite, no futuro, expor a mesma regra de negócio via um worker de fila (ex.: processar webhook) sem duplicar lógica.
- Efeitos colaterais que não são a operação principal (registrar `activity_log` ao mudar status de uma issue, disparar notificação ao mencionar alguém) são chamados explicitamente pelo service dentro da mesma unidade de trabalho — nunca via signal/event mágico implícito que dificulte rastrear o que uma chamada de service realmente faz.

Exemplo de composição real (`IssueService.update`, Sprint 7 — `docs/09-decision-log.md` ADR-012; a autorização de papel geral já foi resolvida no router via `Depends(require_permission(Permission.ISSUE_UPDATE))`, então o service não a repete):
1. Busca a issue via `IssueRepository.get_by_id(workspace_id, issue_id)` → `IssueNotFoundError` se ausente.
2. Se o cliente enviou `If-Match` e o valor diverge de `issue.version` → `IssueVersionConflictError` (409, concorrência otimista), antes de mutar qualquer campo.
3. Para cada campo alterado (`title`, `status`, `priority`, `assignee_id`, ...), registra uma entrada em `ActivityLog` (`field`/`old_value`/`new_value`) com uma `action` específica (`issue.status_changed`, `issue.priority_changed`, `issue.assignee_changed` ou `issue.updated` genérico) — não há validação de transição de estado a aplicar, já que `status` é um enum fixo sem workflow configurável nesta sprint (nenhum `WorkflowStateRepository` existe).
4. Se algo mudou, incrementa `issue.version` e persiste via `IssueRepository.update(issue)` (flush por dirty-tracking do SQLAlchemy, mesma unidade de trabalho da requisição).
5. Retorna a issue atualizada.

A exclusão (`IssueService.delete`) é o único método desta feature que **de fato** consulta `PermissionService` diretamente (em vez de confiar só em `Depends(require_permission(...))` no router): `Permission.ISSUE_DELETE` está em `OWNERSHIP_OVERRIDE_PERMISSIONS` (ADR-010) — "criador da issue ou `ADMIN`+" não é expressável só pela matriz estática de papel, pois depende de `issue.creator_id`, só conhecido após buscar o recurso. O router usa uma dependency mais fraca (`Permission.ISSUE_READ`, que só garante membership) e o service chama `PermissionService.require(member=acting_member, permission=Permission.ISSUE_DELETE, resource_owner_id=issue.creator_id)` depois do fetch — mesmo padrão já usado por `WorkspaceService.require_can_manage_member`.

`CommentService`/`AttachmentService` (Sprint 8 — ADR-013) seguem exatamente o mesmo padrão de posse-como-exceção para `.update`/`.delete` (`comment.update`, `comment.delete`, `attachment.delete`). `LabelService`, por outro lado, não recebe `PermissionService` no `__init__` — toda a autorização de Label é resolvida inteiramente por `Depends(require_permission(...))` no router, sem checagem contextual, porque `label.update`/`label.delete` deliberadamente não têm ownership override (§8.5 de `docs/07-security.md`). `AttachmentService.upload_to_issue` recebe `stream: BinaryIO`, nunca o `UploadFile` do Starlette — o router lê `await file.read()` inteiro em memória antes de chamar o service, mantendo o service agnóstico de HTTP (`CLAUDE.md` §5); um volume de upload maior no futuro trocaria isso por streaming direto ao `StorageProvider` sem mudar a assinatura do service.

## 2. Organização dos Repositories

- Um `Repository` por agregado, definido contra uma interface (`typing.Protocol`) declarada junto ao service que a consome — isso deixa explícito, ao ler um service, exatamente qual conjunto mínimo de operações ele precisa, e permite um `FakeIssueRepository` em memória para testes unitários sem qualquer dependência de banco.
- Métodos usam SQLAlchemy Core/ORM async (`AsyncSession`), sempre parametrizado (nunca concatenação de string em SQL).
- Toda query de leitura aplica `deleted_at IS NULL` por padrão e `workspace_id = :workspace_id` sempre que a tabela tiver essa coluna (todas as tabelas de domínio a partir da Sprint 2 — ver `docs/03-database.md` §4).
- Repository não decide *se* uma operação é permitida (isso é do service/authorization) — decide apenas *como* buscar/persistir.

## 3. Dependency Injection

FastAPI `Depends` é o único mecanismo de DI do projeto (sem container de DI de terceiros — o próprio `Depends` já resolve o grafo de dependências de forma explícita e testável via `app.dependency_overrides` em teste).

Cadeia típica: `get_db_session()` → `get_current_user(session, token)` → `get_issue_repository(session)` → `get_issue_service(repository, ...)`. Cada uma dessas é uma função pura declarada em `core/dependencies.py` ou no módulo da feature (dependências específicas de uma feature vivem na própria feature).

Em teste de contrato (API completa), overrides substituem `get_db_session` por uma sessão contra banco de teste; em teste unitário de service, o service é instanciado diretamente em código Python com repository fake — sem subir FastAPI.

## 4. Exceptions

Ver hierarquia completa em `CLAUDE.md` §7. Detalhe de implementação: o exception handler global é registrado uma única vez em `main.py` via `app.add_exception_handler(FlowDeskError, handler)`, cobrindo toda subclasse automaticamente (Python dispatch por herança) — uma nova exceção de domínio nunca exige registrar um novo handler, apenas herdar da classe correta e (se necessário) mapear seu HTTP status em um dicionário central `EXCEPTION_STATUS_MAP`.

Duas exceções que **não** são de domínio também são traduzidas para o mesmo envelope de erro (`core/exceptions.py`, Sprint 8.7) — sem isso, elas vazariam o formato default do FastAPI/Starlette:

- `RequestValidationError` (corpo/query malformado, capturado pelo próprio FastAPI antes de qualquer schema de domínio ser alcançado) → `request_validation_error_handler`, `code="validation_error"`, 422.
- `starlette.exceptions.HTTPException` (ex.: rota inexistente) → `http_exception_handler`, mapeado por status (`404`→`"not_found"`, `405`→`"method_not_allowed"`, senão `"http_error"`).

## 5. Middleware

Ordem de execução (do mais externo ao mais interno), implementada em `core/middleware.py` e composta em `main.py`:

1. **CORS** — origem permitida = domínio do frontend configurado por ambiente (nunca `*` em produção — `allow_methods`/`allow_headers` também são listas explícitas, não `*`, ver `docs/07-security.md` §5).
2. **Security Headers** (`SecurityHeadersMiddleware`, Sprint 8.7) — `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy` em toda resposta; `Strict-Transport-Security` só quando `ENVIRONMENT=production` (ver `docs/07-security.md` §14).
3. **Request ID** (`RequestIDMiddleware`) — gera/propaga `X-Request-ID`, injeta em contexto de log estruturado via `contextvars`.
4. **Access Log** (`AccessLogMiddleware`, Sprint 8.7) — loga uma linha `http_request` (método, path, status, `duration_ms`) ao final de cada requisição; também reseta o contexto de `user_id` no início de cada requisição (`get_current_user`, em `core/dependencies.py`, o preenche quando a requisição é autenticada).
5. **Rate limiting** (`RateLimitMiddleware`) — checagem contra Redis (janela deslizante) antes de qualquer processamento de negócio; aplica-se por IP em rotas anônimas (`/auth/login`) e por usuário autenticado nas demais.

Middlewares são funções puras compostas na criação da app (`main.py`), nunca acopladas a uma feature específica.

## 6. Validações

- Toda entrada de rota é um schema Pydantic (`XxxRequest`), validado automaticamente pelo FastAPI antes do handler ser chamado — nunca há `if not payload.get("field")` manual no código de negócio.
- Regras de validação que dependem de estado do banco (unicidade de e-mail, existência de FK referenciada) **não** vivem no schema Pydantic (que só valida a forma do dado isoladamente) — vivem no service, que já tem acesso ao repository, e resultam em exceção de domínio (`ConflictError`/`NotFoundError`), não em `422`.
- Schemas de request e de response são tipos **distintos**, mesmo quando parecidos (`IssueCreateRequest` vs. `IssueResponse`) — nunca reusar o mesmo schema para entrada e saída, pois os campos obrigatórios/computados diferem (ex.: `number` e `id` não existem na criação, existem na resposta).

## 7. Autenticação (implementação)

- Hash de senha: Argon2id via `passlib`/`argon2-cffi`, parâmetros de custo revisados a cada major version do projeto (documentado em `docs/07-security.md`).
- JWT assinado com chave assimétrica (`RS256`) — permite que, no futuro, outros serviços validem o token com a chave pública sem precisarem do segredo de assinatura, caso o sistema cresça para múltiplos serviços.
- Claims mínimos no access token: `sub` (user_id), `iat`, `exp`, `jti`. Nenhum dado de workspace/papel embutido no token — papel é sempre resolvido em tempo real contra `workspace_members` (evita token "stale" carregando uma permissão já revogada).

**Implementado na Sprint 3** (`docs/09-decision-log.md` ADR-008 tem o racional de cada desvio): `core/security.py` (hash/verify Argon2id, criação/decodificação de JWT, geração e hash de refresh token), `core/dependencies.py` (`get_current_user`, `get_user_repository`, `get_session_repository`), `core/rate_limit.py` + `RateLimitMiddleware` em `core/middleware.py`, e a feature `features/auth/` completa (`schemas.py`/`service.py`/`router.py`, além do `models.py`/`repository.py` já existentes da Sprint 2). `features/users/` é uma feature nova e enxuta só com `GET /users/me`, reaproveitando o `UserRepository` do auth em vez de duplicá-lo — o perfil do usuário é o mesmo agregado, exposto sob um path de recurso diferente por convenção de nomenclatura (`docs/04-api-design.md` §2.1).

## 8. Autorização — RBAC (implementação, Sprint 5)

- `core/permissions.py` expõe o catálogo central `Permission` (`enum.StrEnum`, ex.: `Permission.WORKSPACE_UPDATE = "workspace.update"`) — toda permissão do sistema é um membro deste enum, nunca uma string solta espalhada por routers/services.
- `core/authorization.py` expõe:
  - `ROLE_PERMISSIONS: dict[WorkspaceRole, frozenset[Permission]]` — a matriz estática por papel (ver `docs/07-security.md` §8 para a matriz completa e a justificativa de cada linha).
  - `OWNERSHIP_OVERRIDE_PERMISSIONS: frozenset[Permission]` — permissões concedidas a qualquer papel quando o chamador é o dono do recurso (`comment.update`, `comment.delete`, `issue.delete`), independente do que a matriz base diz.
  - `PermissionService.can(member: WorkspaceMember, permission: Permission, resource_owner_id: UUID | None = None) -> bool` / `.require(...)` (lança `PermissionDeniedError`) — o único ponto de decisão de autorização do sistema.
  - `PermissionService.can_manage_member(actor_role, target_role) -> bool` / `.require_can_manage_member(...)` (lança `CannotManageOwnerError`) — regra contextual ("ADMIN não gerencia OWNER") não expressável na matriz estática porque depende do papel de um recurso já buscado pelo service.
  - `WorkspaceContext` (dataclass `workspace` + `member`) e `get_workspace_context(workspace_id, ...)` — resolve a etapa "Workspace Context" do fluxo (`CLAUDE.md` §10): confirma posse de tenant antes de qualquer permissão específica ser avaliada, levantando `WorkspaceNotFoundError` (404) para não-membro ou workspace inexistente.
  - `require_permission(permission: Permission)` — factory de dependency do FastAPI que compõe `get_workspace_context` + `PermissionService.require`, usada declarativamente na assinatura da rota (`Depends(require_permission(Permission.WORKSPACE_UPDATE))`, `CLAUDE.md` §10). Retorna a `WorkspaceMember` do chamador para o router reaproveitar (ex.: repassar `.role` a uma checagem contextual do service).
- **Exceção deliberada de camadas**: `core/authorization.py` importa `features.workspaces.{models,repository,exceptions}` — toda decisão de permissão depende de resolver a associação do chamador com o workspace, e duplicar essa resolução em cada feature futura (issues, comments, projects) seria a reimplementação que esta sprint elimina. Ver ADR-010 em `docs/09-decision-log.md`.
- Services **não** checam papel/permissão — essa responsabilidade saiu inteiramente para a camada de `Depends` (e, quando dependente de um recurso já buscado, para uma chamada explícita a `PermissionService` dentro do próprio service). Um service que recebe uma chamada já passou pela checagem.

## 9. Logs

Ver `CLAUDE.md` §9 para o padrão. Implementação: `structlog` configurado em `core/logging.py`, processadores adicionam `request_id`, `user_id` (ambos via `contextvars`, propagados pelo `RequestIDMiddleware`/`AccessLogMiddleware`/`get_current_user` — Sprint 8.7) e `environment` (fixado uma vez em `configure_logging`, não por `contextvar`, já que não varia por requisição), timestamp ISO, e renderizam JSON em produção / formato legível colorido em desenvolvimento (mesma configuração, `renderer` trocado por variável de ambiente). Todo log carrega os três campos quando aplicável — nenhum evento de negócio precisa declará-los manualmente.

## 10. Configuração

- `core/config.py`: classe `Settings(BaseSettings)` do Pydantic, carrega de variáveis de ambiente (`.env` em desenvolvimento, variáveis reais de ambiente em produção — nunca `.env` committado; `.env.example` documenta as chaves esperadas).
- Falha rápida: a aplicação não sobe se uma variável obrigatória (`DATABASE_URL`, `JWT_PRIVATE_KEY`, `REDIS_URL`) estiver ausente — validado na construção do `Settings`, antes de qualquer rota estar disponível. `environment` é um `Literal["development", "test", "production"]` (não `str` livre) — um valor fora desse conjunto também falha na inicialização. Um segundo validador (`_forbid_dev_key_in_production`, Sprint 8.7) recusa subir com `ENVIRONMENT=production` se `JWT_PUBLIC_KEY` ainda for o par de chaves de desenvolvimento checado em `.env.example` (ADR-008/ADR-016).
- Configuração é lida uma vez no startup e injetada via `Depends(get_settings)` onde necessário (cacheada com `lru_cache`) — nunca `os.getenv` disperso pelo código.

### Referência de variáveis de ambiente (backend)

| Variável | Obrigatória | Default | Descrição |
|---|---|---|---|
| `ENVIRONMENT` | não | `development` | `development` \| `test` \| `production` — controla formato de log (JSON vs. legível) e os validadores de produção. |
| `LOG_LEVEL` | não | `INFO` | Nível mínimo de log (`DEBUG`/`INFO`/`WARNING`/`ERROR`). |
| `DATABASE_URL` | **sim** | — | DSN async do Postgres (`postgresql+asyncpg://...`). |
| `REDIS_URL` | **sim** | — | DSN do Redis (rate limit). |
| `CORS_ORIGINS` | não | `http://localhost:5173` | Lista separada por vírgula de origens permitidas. |
| `JWT_PRIVATE_KEY` / `JWT_PUBLIC_KEY` | **sim** | — | Par RS256 (PEM com `\n` escapado), nunca o par de dev em produção (ver acima). |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | não | `15` | Vida útil do access token. |
| `REFRESH_TOKEN_EXPIRE_DAYS` | não | `30` | Vida útil do refresh token. |
| `INVITATION_EXPIRE_DAYS` | não | `7` | Vida útil de um convite de workspace. |
| `PASSWORD_RESET_TOKEN_EXPIRE_MINUTES` | não | `30` | Vida útil de um token de recuperação de senha (RF-AUTH-06, Sprint 9) — curta de propósito, ver ADR-017. |
| `UPLOAD_DIR` | não | `var/uploads` | Diretório local de anexos (`core/storage.py::LocalStorageProvider`). |
| `MAX_UPLOAD_SIZE_BYTES` | não | `10485760` (10 MB) | Teto de tamanho de um anexo. |
| `ALLOWED_UPLOAD_CONTENT_TYPES` | não | ver `core/config.py` | Lista branca de `Content-Type` separada por vírgula. |

## 11. Projetos (implementação, Sprint 6)

- `features/projects/` segue o esqueleto padrão de toda feature (`models.py`, `schemas.py`, `service.py`, `repository.py`, `router.py`, `exceptions.py`, `dependencies.py`) — RF-PROJ-01, camada de service/router sobre o schema já modelado na Sprint 2 (`docs/03-database.md` §6.2).
- `ProjectService` **não** recebe `PermissionService` injetado, ao contrário de `WorkspaceService` (§8 acima): não há regra de autorização contextual para Projetos (sem ownership override, sem "ADMIN não gerencia X") — toda decisão de acesso é resolvida inteiramente por `Depends(require_permission(Permission.PROJECT_X))` no router, então o service não tem checagem própria a fazer. Menos código aqui é reflexo direto de o domínio não ter regra contextual a resolver, não uma omissão.
- `ProjectRepository.has_active_issues()` (usada pela regra de exclusão bloqueada por issues ativas) é escrita com SQLAlchemy Core (`sqlalchemy.table()`/`column()`) contra a tabela `issues` por nome, em vez de importar o model ORM `Issue` — importar `Issue` forçaria o SQLAlchemy a configurar todo o grafo de mapeamento dele (inclusive a relação com `Comment`) como efeito colateral de só carregar `ProjectRepository`, o que quebra hoje porque `features/comments/` ainda não está registrada em `main.py`. Ver ADR-011 em `docs/09-decision-log.md`.
- `core/slug.py` (`slugify()`, `validate_slug_format()`): extração, nesta sprint, da lógica de slug que antes vivia duplicada como função privada em `WorkspaceService` — `ProjectService` e `WorkspaceService` (junto dos schemas `WorkspaceCreateRequest`/`WorkspaceUpdateRequest`) agora importam do mesmo módulo em vez de reimplementar a transliteração via `unicodedata`.
- `src/db/models_registry.py`: corrige um bug latente pré-existente à Sprint 6. Relationships declaradas por string entre features (`Project.issues -> "Issue"`, `Issue.comments -> "Comment"`) só resolvem quando toda classe alvo já foi importada em algum ponto do processo — `main.py` só importava os models alcançáveis a partir dos routers já registrados (nunca Comments/Labels/Teams/Notifications/Attachments), o que fazia qualquer instanciação real de `Project`/`Issue` lançar `sqlalchemy.exc.InvalidRequestError`. A lista de imports já existia em `db/migrations/env.py` (para o autogenerate do Alembic); extraída para este módulo único, importado por ambos. Ver ADR-011.

## 12. Comentários, Labels e Anexos (implementação, Sprint 8)

- `features/comments/`, `features/labels/` e `features/attachments/` seguem o esqueleto padrão de toda feature, todos os três agora registrados em `main.py` (o que resolve, de fato, a limitação apontada em §11 acima). Ver ADR-013 em `docs/09-decision-log.md` para o racional completo de cada decisão de desenho.
- `CommentService._resolve_mentions`: extrai menções via regex (`@([A-Za-z0-9._%+-]+)`) sobre o `body` e casa cada token contra o local-part (parte antes do `@`) do e-mail dos membros do workspace — não contra o nome de exibição (não único) nem via UI de autocomplete (fora de escopo). Resolução limitada aos primeiros 200 membros (`_MENTION_MEMBER_LOOKUP_LIMIT`) via uma única query (`WorkspaceRepository.list_members`), evitando N+1; suficiente para a escala deste projeto, uma busca indexada por local-part seria a evolução natural para workspaces muito maiores.
- `LabelService` não recebe `PermissionService` injetado, mesmo racional de `ProjectService` (§11): `label.update`/`label.delete` não têm ownership override, então toda autorização é resolvida por `Depends(require_permission(...))` no router.
- `AttachmentService.upload_to_issue` recebe `storage: StorageProvider` (`core/storage.py`, `Protocol`) injetado — `LocalStorageProvider` é a única implementação nesta sprint (disco local sob `Settings.upload_dir`), mas o service nunca importa essa classe concreta diretamente, só o protocolo, deixando a troca por um provider `"s3"` futuro restrita a `core/storage.py` + `core/dependencies.py`, sem tocar `AttachmentService`. `Attachment.storage_key` é sempre um ponteiro opaco (nome gerado, prefixado por UUID) — nunca o nome original do arquivo nem um path absoluto vazado para fora dessa camada.
- `core/validators.py::validate_hex_color`: extraída de `features/projects/schemas.py` (Sprint 6) porque `LabelCreateRequest`/`LabelUpdateRequest` precisam exatamente da mesma validação — mesmo racional já aplicado a `core/slug.py` (§11).

## 13. Health Checks (implementação, Sprint 8.7)

- `GET /health` (liveness) permanece um retorno fixo (`{"status": "ok"}`) — só confirma que o processo aceita conexões, sem depender de nenhuma dependência externa. É o que um orquestrador usa para decidir se reinicia o container.
- `GET /health/ready` (readiness) roda `core/health.py::run_health_checks()` — checagens concorrentes (`asyncio.gather`) de banco (`SELECT 1` via `core/db.py::ping_database`), Redis (`PING` via `core/rate_limit.py::ping_redis`) e do diretório de upload (existe e é gravável). Responde 503 se qualquer checagem falhar, para que um load balancer pare de rotear tráfego para esta instância antes que ela receba uma requisição real e falhe.
- Esta rota não é autenticada (um orquestrador não consegue autenticar um probe) e fica fora de `_API_PREFIX`, logo fora do `RateLimitMiddleware` — por isso o texto completo de uma falha (`str(exc)`, que pode conter host/porta/detalhe de driver) nunca vai no corpo da resposta HTTP, só no log estruturado (`health_check_failed`). O campo `detail` de cada checagem só é populado na resposta quando `not settings.is_production`.
- Adicionar uma nova dependência externa (ex.: um provider de storage remoto) é uma função de checagem nova + uma linha em `run_health_checks` — o registro foi desenhado para isso, sem precisar tocar `/health/ready` em si.
- `GET /version` inclui `uptime_seconds` (calculado a partir de um timestamp de `time.monotonic()` guardado em `app.state` no `lifespan`) — útil para detectar reinícios inesperados sem depender de log externo.

## 14. Observabilidade e Métricas (implementação, Sprint 14.5)

- `GET /metrics` (`docs/09-decision-log.md` ADR-031) — contagem de requisições/erros 5xx e latência p95 por endpoint, agregados a partir de contadores/amostras mantidos no Redis, não um exportador Prometheus (fora de escopo, ADR-016). Mesmo precedente de `/health`/`/health/ready`: não autenticado, fora de `_API_PREFIX`.
- `core/metrics.py::record_request` é chamado por `AccessLogMiddleware` (`core/middleware.py`) depois de logar `http_request`, reaproveitando o `duration_ms`/`status_code` já calculados ali. Agrupa por `request.scope["route"].path` (o template da rota, ex. `/workspaces/{workspace_id}/issues`), não o path com IDs reais — requisições sem rota casada (404 genuíno) caem sob o rótulo `<unmatched>` para não deixar sondagem externa crescer o conjunto de rotas rastreadas sem limite.
- `p95` é calculado em leitura (`core/metrics.py::get_metrics_snapshot`) sobre no máximo 1000 amostras recentes por endpoint (lista Redis capada via `RPUSH`+`LTRIM`) — uma janela móvel aproximada, não uma janela por tempo fixa nem um histograma. Contagens de requisição/5xx são cumulativas desde a última vez que o Redis foi limpo/reiniciado.
- `core/redis_client.py::get_redis()` — cliente Redis com escopo por event loop, extraído de `core/rate_limit.py` nesta sprint quando `core/metrics.py` passou a precisar do mesmo cliente; `rate_limit.py` foi atualizado para importar em vez de duplicar.
