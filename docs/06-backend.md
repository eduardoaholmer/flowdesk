# 06 — Backend

Stack: Python 3.12, FastAPI, SQLAlchemy 2.0 (async), Alembic, Pydantic v2, PostgreSQL, Redis, Poetry, Pytest. Este documento detalha a organização interna; o fluxo de camadas normativo está em `CLAUDE.md` §3–§11 — aqui aprofundamos *como* cada peça é implementada.

## 1. Organização dos Services

- Um `Service` por agregado de domínio, instanciado por requisição via DI (nunca singleton com estado mutável entre requisições).
- Assinatura típica de método: recebe `workspace_id`, o `CurrentUser` (autenticado, já resolvido pela camada de DI) e um DTO de entrada; retorna a entidade de domínio (model ORM) ou uma dataclass de resultado.
- Services não têm conhecimento de `Request`/`Response` do FastAPI nem de status HTTP — o mapeamento para HTTP é responsabilidade do router + exception handler global. Isso é o que permite, no futuro, expor a mesma regra de negócio via um worker de fila (ex.: processar webhook) sem duplicar lógica.
- Efeitos colaterais que não são a operação principal (registrar `activity_log` ao mudar status de uma issue, disparar notificação ao mencionar alguém) são chamados explicitamente pelo service dentro da mesma unidade de trabalho — nunca via signal/event mágico implícito que dificulte rastrear o que uma chamada de service realmente faz.

Exemplo de composição (`IssueService.update_status`):
1. Busca a issue via `IssueRepository.get_by_id(workspace_id, issue_id)` → `NotFoundError` se ausente.
2. Verifica `can(user, "issue:update", issue)` → `PermissionDeniedError`.
3. Valida a transição contra o workflow do time via `WorkflowStateRepository` → `ConflictError` (`invalid_status_transition`) se inválida.
4. Persiste via `IssueRepository.update_status(issue, novo_status)`.
5. Registra `ActivityLogRepository.record(...)` na mesma transação (Unit of Work).
6. Retorna a issue atualizada.

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

## 5. Middleware

Ordem de execução (do mais externo ao mais interno):

1. **CORS** — origem permitida = domínio do frontend configurado por ambiente (nunca `*` em produção, ver `docs/07-security.md`).
2. **Request ID** — gera/propaga `X-Request-ID`, injeta em contexto de log estruturado.
3. **Rate limiting** — checagem contra Redis (janela deslizante) antes de qualquer processamento de negócio; aplica-se por IP em rotas anônimas (`/auth/login`) e por usuário autenticado nas demais.
4. **Logging de acesso** — loga método, path, status, duração, `request_id`, `user_id` ao final da requisição.

Middlewares são funções puras compostas na criação da app (`main.py`), nunca acopladas a uma feature específica.

## 6. Validações

- Toda entrada de rota é um schema Pydantic (`XxxRequest`), validado automaticamente pelo FastAPI antes do handler ser chamado — nunca há `if not payload.get("field")` manual no código de negócio.
- Regras de validação que dependem de estado do banco (unicidade de e-mail, existência de FK referenciada) **não** vivem no schema Pydantic (que só valida a forma do dado isoladamente) — vivem no service, que já tem acesso ao repository, e resultam em exceção de domínio (`ConflictError`/`NotFoundError`), não em `422`.
- Schemas de request e de response são tipos **distintos**, mesmo quando parecidos (`IssueCreateRequest` vs. `IssueResponse`) — nunca reusar o mesmo schema para entrada e saída, pois os campos obrigatórios/computados diferem (ex.: `number` e `id` não existem na criação, existem na resposta).

## 7. Autenticação (implementação)

- Hash de senha: Argon2id via `passlib`/`argon2-cffi`, parâmetros de custo revisados a cada major version do projeto (documentado em `docs/07-security.md`).
- JWT assinado com chave assimétrica (`RS256`) — permite que, no futuro, outros serviços validem o token com a chave pública sem precisarem do segredo de assinatura, caso o sistema cresça para múltiplos serviços.
- Claims mínimos no access token: `sub` (user_id), `iat`, `exp`, `jti`. Nenhum dado de workspace/papel embutido no token — papel é sempre resolvido em tempo real contra `workspace_members` (evita token "stale" carregando uma permissão já revogada).

## 8. Autorização (implementação)

- `core/authorization.py` expõe `can(user: CurrentUser, action: str, resource: Resource) -> bool`, implementada como consulta a uma matriz estática `PERMISSION_MATRIX: dict[Role, set[str]]` (ver `docs/07-security.md` para a matriz completa) combinada com checagens contextuais (ex.: `"comment:delete"` é permitido ao autor independentemente do papel).
- `require_permission(action: str)` é uma factory de dependency do FastAPI que resolve o recurso-alvo (via path param), chama `can`, e lança `PermissionDeniedError` se negado — usada declarativamente na assinatura da rota (`CLAUDE.md` §10).

## 9. Logs

Ver `CLAUDE.md` §9 para o padrão. Implementação: `structlog` configurado em `core/logging.py`, processadores adicionam `request_id` (via `contextvars`, propagado pelo middleware), timestamp ISO, e renderizam JSON em produção / formato legível colorido em desenvolvimento (mesma configuração, `renderer` trocado por variável de ambiente).

## 10. Configuração

- `core/config.py`: classe `Settings(BaseSettings)` do Pydantic, carrega de variáveis de ambiente (`.env` em desenvolvimento, variáveis reais de ambiente em produção — nunca `.env` committado; `.env.example` documenta as chaves esperadas).
- Falha rápida: a aplicação não sobe se uma variável obrigatória (`DATABASE_URL`, `JWT_PRIVATE_KEY`, `REDIS_URL`) estiver ausente — validado na construção do `Settings`, antes de qualquer rota estar disponível.
- Configuração é lida uma vez no startup e injetada via `Depends(get_settings)` onde necessário (cacheada com `lru_cache`) — nunca `os.getenv` disperso pelo código.
