# CLAUDE.md — Manual de Engenharia do FlowDesk

> Este documento é a **fonte de verdade** do projeto. Qualquer implementação — feature, refactor, correção de bug — deve obedecer ao que está aqui descrito. Se uma decisão de código conflitar com este manual, o manual vence, e o manual só muda por meio de uma atualização explícita (com uma entrada em `docs/09-decision-log.md`).
>
> Este arquivo não repete os documentos em `docs/`. Ele define **como trabalhamos**; os documentos em `docs/` definem **o que estamos construindo**. Leia sempre em conjunto:
> - `docs/02-architecture.md` — arquitetura em profundidade
> - `docs/03-database.md` — modelo de dados
> - `docs/04-api-design.md` — contrato de API
> - `docs/06-backend.md` / `docs/05-frontend.md` — organização interna de cada app
> - `docs/07-security.md` — segurança
> - `docs/10-coding-standards.md` — padrões de código detalhados

---

## 1. Filosofia do projeto

FlowDesk é um clone de propósito de portfólio do Linear (gestão de issues/projetos para times de produto), mas não é um exercício de "copiar telas". O objetivo real é **demonstrar critério de engenharia sênior**: arquitetura em camadas, separação de responsabilidades, segurança correta em um SaaS multi-tenant, e código que um time consegue manter em produção por anos.

Princípios que guiam toda decisão neste projeto, em ordem de prioridade:

1. **Clareza sobre esperteza.** Código que exige um comentário para ser entendido geralmente está mal escrito. Preferimos nomes explícitos e funções pequenas a abstrações genéricas "para o futuro".
2. **Previsibilidade estrutural.** Toda feature segue o mesmo esqueleto (rota → schema → service → repository → model). Um novo desenvolvedor deve conseguir prever onde um arquivo está antes de procurá-lo.
3. **Fronteiras explícitas.** Camadas não pulam etapas. Uma rota nunca fala com o banco diretamente; um repository nunca contém regra de negócio. Isso não é dogma — é o que torna o sistema testável em isolamento.
4. **Segurança não é uma etapa posterior.** Isolamento de workspace, RBAC e validação de entrada são tratados como requisito funcional desde o primeiro schema, não como hardening de última hora.
5. **Justificar, não copiar.** Cada escolha de tecnologia neste projeto tem uma razão registrada em `docs/09-decision-log.md`. "É popular" não é motivo suficiente — precisa resolver um problema real deste sistema.
6. **YAGNI com limites.** Não construímos generalidade especulativa (multi-banco de dados, plugins, feature flags elaboradas) só porque "produtos grandes têm isso". Construímos o que o roadmap em `docs/08-roadmap.md` realmente pede, com pontos de extensão nos lugares onde o domínio (não a tecnologia) sugere que a mudança é provável — por exemplo, workflow de status por time.

---

## 2. Stack tecnológico (decisão fundacional)

Esta stack é vinculante para todo o projeto. Justificativas completas estão em `docs/09-decision-log.md` (ADR-001 a ADR-006).

| Camada | Escolha | Alternativas consideradas |
|---|---|---|
| Linguagem backend | Python 3.12 | Node/TypeScript (rejeitado: ver ADR-001) |
| Framework backend | FastAPI | Django REST Framework, Flask |
| ORM | SQLAlchemy 2.0 (async) + Alembic | Django ORM, Tortoise ORM, SQLModel |
| Validação/Schemas | Pydantic v2 | Marshmallow |
| Banco de dados | PostgreSQL 16 | MySQL, MongoDB |
| Cache / filas leves / rate limit | Redis 7 | Memcached |
| Autenticação | JWT (access) + Refresh Token rotativo em cookie HttpOnly | Sessão pura em servidor, Auth0/Clerk gerenciado |
| Gerenciador de dependências (backend) | Poetry | pip + requirements.txt |
| Lint/format (backend) | Ruff + Mypy | Flake8 + Black + isort separados |
| Testes (backend) | Pytest + pytest-asyncio + httpx | unittest |
| Linguagem frontend | TypeScript 5 | JavaScript puro |
| Framework frontend | React 19 + Vite (SPA) | Next.js (App Router) — ver ADR-003 |
| Roteamento | React Router v6 | TanStack Router |
| Estado de servidor | TanStack Query | Redux + RTK Query |
| Estado de cliente | Zustand | Redux, Context API puro |
| Formulários | React Hook Form + Zod | Formik |
| UI Kit | Tailwind CSS + shadcn/ui (Radix primitives) | Chakra UI, MUI |
| Testes (frontend) | Vitest + Testing Library + Playwright (E2E) | Jest + Cypress |
| Monorepo | pastas independentes (`backend/`, `frontend/`, `docs/`) — sem workspace de package manager compartilhado, já que só o frontend usa npm | Repositórios separados, ou `apps/api`/`apps/web` sob pnpm workspaces |

Por que Python no backend e não manter uma stack 100% TypeScript (o que simplificaria o monorepo)? Porque parte do valor de portfólio deste projeto é demonstrar competência em **dois ecossistemas de produção** distintos, incluindo os padrões de tipagem, validação e concorrência assíncrona do Python moderno — ver ADR-001 para o racional completo, incluindo os trade-offs que isso custa (dois toolchains, sem compartilhamento de tipos automático).

---

## 3. Arquitetura em camadas (backend)

Fluxo obrigatório de uma requisição:

```
Cliente → Middleware (CORS, request-id, logging) → Router (FastAPI) → Schema (Pydantic, validação de entrada)
        → Dependency Injection (auth, sessão de DB, permissões) → Service (regra de negócio)
        → Repository (acesso a dados) → Model (SQLAlchemy) → PostgreSQL
        ← Schema de resposta (Pydantic) ← Service ← Repository
← Response envelope padronizado ← Exception handler (se aplicável)
```

Regras inegociáveis:

- **Router** não contém lógica de negócio. Sua única responsabilidade é: desserializar/validar entrada (via schema), resolver dependências (usuário autenticado, sessão de DB), chamar **um único método de service**, e devolver o resultado. Um router nunca importa um Repository diretamente.
- **Service** contém toda a regra de negócio e orquestra um ou mais repositories. Services não conhecem o protocolo HTTP (não recebem `Request`, não lançam `HTTPException` — lançam exceções de domínio, ver §7).
- **Repository** é a única camada que fala SQL/ORM. Não contém regra de negócio, apenas consultas e persistência. Repositories recebem `workspace_id` explicitamente em qualquer método que leia/escreva dados com escopo de tenant — nunca inferem isolamento implicitamente.
- **Model** representa a tabela. Pode conter apenas comportamento trivial derivado de dados (`@property`), nunca regra de negócio ou I/O.
- Uma camada só pode chamar a camada imediatamente abaixo dela. Isso é validado em code review (ver checklist §14).

Detalhamento completo, incluindo diagramas, está em `docs/02-architecture.md` e `docs/06-backend.md`.

---

## 4. Padrão de criação de rotas

Cada recurso vive em `backend/src/features/<recurso>/router.py`. Estrutura de um endpoint:

```python
router = APIRouter(prefix="/workspaces/{workspace_id}/issues", tags=["issues"])

@router.post("", status_code=201, response_model=IssueResponse)
async def create_issue(
    workspace_id: UUID,
    payload: IssueCreateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    service: IssueService = Depends(get_issue_service),
) -> IssueResponse:
    issue = await service.create(workspace_id, current_user, payload)
    return IssueResponse.model_validate(issue)
```

Convenções:

- Prefixo de recurso sempre no plural (`/issues`, não `/issue`).
- Recursos com escopo de tenant sempre aninhados sob `/workspaces/{workspace_id}/...` — nunca um endpoint global que dependa de um header implícito para isolamento (ver `docs/07-security.md`).
- Um router por recurso; um arquivo nunca mistura dois recursos.
- Toda rota declara `response_model` explícito — nunca retorna o model do ORM diretamente.
- Autorização (RBAC) é resolvida via `Depends`, nunca com `if` manual espalhado no corpo da rota (ver §8).
- Rotas não tratam exceções manualmente; exceções de domínio sobem para o exception handler global (§7).

---

## 5. Padrão de Services

- Um service por agregado de domínio (`IssueService`, `WorkspaceService`, `AuthService`...), nunca um "God Service".
- Métodos de service recebem tipos primitivos/DTOs de entrada (schemas Pydantic ou dataclasses internas) e retornam models de domínio (ORM) ou dataclasses — nunca schemas de resposta HTTP. Quem serializa para HTTP é o router.
- Services recebem seus repositories via injeção de dependência no `__init__`, nunca instanciam repositories internamente. Isso é o que torna o service testável com repositories fake/mocados, sem subir banco.
- Toda regra de negócio (transições de estado, validações que dependem de outras entidades, side effects como notificações) mora aqui — nunca no router, nunca no repository.
- Um método de service = uma transação de negócio. Se precisar orquestrar múltiplos repositories, o service controla o boundary da transação (`async with uow:`), não o router.

---

## 6. Padrão de Repositories

- Um repository por agregado (`IssueRepository`, `CommentRepository`...), implementando uma interface mínima explícita (`Protocol` em Python) para permitir fakes em teste.
- Métodos expõem operações de domínio (`get_by_id`, `list_by_team`, `create`, `soft_delete`), nunca vazam detalhes de query para quem chama (não retornam `Query` do SQLAlchemy).
- Todo método que lê ou escreve dado com escopo de workspace recebe `workspace_id` como parâmetro obrigatório e o aplica no `WHERE` — isolamento multi-tenant é reforçado na camada de dados, não confiado apenas à regra de negócio (defesa em profundidade, ver `docs/07-security.md`).
- Soft delete é sempre via `deleted_at`; repositories filtram `deleted_at IS NULL` por padrão em todo método de leitura, exigindo um parâmetro explícito (`include_deleted=True`) para o caso raro contrário.
- Repositories não fazem `commit()` — quem controla o boundary transacional é o service (ou um Unit of Work explícito para operações multi-repository).

---

## 7. Padrão de Exceptions

Hierarquia de exceções de domínio (`backend/src/core/exceptions.py`), todas herdando de `FlowDeskError`:

```
FlowDeskError (base, nunca lançada diretamente)
├── NotFoundError            → HTTP 404
├── ValidationError          → HTTP 422
├── ConflictError            → HTTP 409   (ex.: e-mail duplicado, versão otimista divergente)
├── PermissionDeniedError    → HTTP 403
├── AuthenticationError      → HTTP 401
└── RateLimitedError         → HTTP 429
```

- Services e repositories lançam exceções de domínio, nunca `HTTPException` do FastAPI — isso mantém a camada de negócio agnóstica de protocolo (poderia ser reusada por um worker assíncrono ou CLI no futuro).
- Um único exception handler global (registrado em `main.py`) traduz exceção de domínio → `ErrorResponse` padronizado (§8 de `docs/04-api-design.md`) com o HTTP status correto.
- Exceções sempre carregam um `code` machine-readable (`"issue_not_found"`) além da mensagem — o frontend nunca deve fazer `if (message === "...")`.
- Nunca capturar `Exception` genérica para "engolir" erro. Exceções não mapeadas propagam e viram 500 com log estruturado (§9); isso é intencional — erro não tratado deve ser visível, não silencioso.

---

## 8. Padrão de Responses

Toda resposta de sucesso e erro segue um envelope consistente:

```json
// Sucesso (recurso único)
{ "data": { "...": "..." } }

// Sucesso (coleção paginada)
{
  "data": [ { "...": "..." } ],
  "meta": { "page": 1, "per_page": 20, "total": 134, "total_pages": 7 }
}

// Erro
{
  "error": {
    "code": "issue_not_found",
    "message": "Issue não encontrada.",
    "details": null
  }
}
```

- `code` é estável e versionado por contrato — mudar seu valor é uma breaking change de API.
- `details` carrega estrutura adicional apenas para erros de validação (lista de campo + motivo), nunca stack trace.
- Datas sempre em ISO 8601 UTC. IDs sempre UUID em string.
- Justificativa completa e exemplos por recurso em `docs/04-api-design.md`.

---

## 9. Padrão de Logs

- Logging estruturado em JSON (via `structlog`), nunca `print()` ou string formatada solta.
- Todo log carrega, no mínimo: `timestamp`, `level`, `request_id`, `user_id` (quando autenticado), `workspace_id` (quando aplicável), `event`.
- Níveis: `DEBUG` (detalhe de desenvolvimento, desligado em produção), `INFO` (eventos de negócio relevantes: issue criada, usuário logado), `WARNING` (situação recuperável: rate limit atingido), `ERROR` (exceção não tratada, falha de integração).
- Nunca logar segredos, senhas, tokens completos ou payloads de autenticação. Tokens são logados truncados/hasheados quando a correlação for necessária.
- `request_id` é gerado no middleware de entrada e propagado em todo log daquela requisição, permitindo rastrear uma requisição ponta a ponta.

---

## 10. Padrão de Permissões (RBAC)

- Papéis por workspace: `OWNER`, `ADMIN`, `MEMBER`, `GUEST` (definição completa e matriz de permissões em `docs/07-security.md`).
- Permissões são resolvidas por uma função pura `can(user, action, resource) -> bool` centralizada em `core/authorization.py`, nunca reimplementada localmente em um service.
- Toda rota que precisa de autorização declara isso via `Depends(require_permission("issue:delete"))` — a checagem acontece antes do service ser chamado, nunca depois.
- Autorização é sempre verificada contra o **workspace do recurso**, nunca assumida a partir do workspace "ativo" enviado pelo cliente sem validação servidor-side.

---

## 11. Padrão de autenticação

- Login emite um **access token JWT** de vida curta (15 min) devolvido no corpo da resposta (mantido em memória no frontend, nunca em `localStorage`) e um **refresh token** opaco, rotativo, armazenado hasheado no banco e entregue como cookie `HttpOnly + Secure + SameSite=Strict`.
- Renovação de sessão via `POST /auth/refresh`, protegido por CSRF token de dupla submissão (o refresh token trafega só em cookie; um cookie não-HttpOnly com o CSRF token deve acompanhar o header em toda chamada mutável).
- Logout revoga o refresh token no banco (não é só apagar cookie no cliente).
- Detalhes completos, incluindo rotação e detecção de reuso de refresh token, em `docs/07-security.md`.

---

## 12. Organização das Features (Feature-based, não layer-based no nível superior)

Backend e frontend organizam código **por feature de domínio**, não por tipo técnico no nível raiz — dentro de cada feature, sim, há sub-organização técnica (router/service/repository ou components/hooks). Isso evita que uma pasta `services/` global cresça sem fronteira e force acoplamento entre domínios não relacionados.

Ver estrutura completa em §13 abaixo e detalhamento em `docs/05-frontend.md` / `docs/06-backend.md`.

---

## 13. Estrutura de pastas

### Backend (`backend`)

```
backend/
├── src/
│   ├── core/                  # transversal: config, db session, exceptions, authorization, security (jwt/hash), logging
│   ├── features/
│   │   ├── auth/              # router, service, schemas, exceptions específicas
│   │   ├── workspaces/
│   │   ├── teams/
│   │   ├── projects/
│   │   ├── issues/
│   │   │   ├── router.py
│   │   │   ├── service.py
│   │   │   ├── repository.py
│   │   │   ├── schemas.py
│   │   │   └── models.py
│   │   ├── comments/
│   │   ├── labels/
│   │   ├── cycles/
│   │   └── notifications/
│   ├── main.py                 # cria app, registra routers, middlewares, exception handlers
│   └── db/
│       ├── base.py             # Base declarativa, mixins (UUID, timestamps, soft delete)
│       └── migrations/         # Alembic
├── tests/
│   ├── unit/                   # services com repositories fake
│   ├── integration/            # repositories com banco de teste real
│   └── contract/               # API completa via httpx AsyncClient
└── pyproject.toml
```

### Frontend (`frontend`)

```
frontend/
├── src/
│   ├── app/                     # bootstrap: App.tsx, providers.tsx (QueryClient, tema, tooltips), router.tsx
│   ├── pages/                   # composição fina por rota (HomePage, NotFoundPage, ...)
│   ├── features/
│   │   ├── auth/
│   │   │   ├── components/
│   │   │   ├── hooks/
│   │   │   ├── api.ts           # chamadas TanStack Query desse domínio
│   │   │   └── types.ts
│   │   ├── workspaces/
│   │   ├── issues/
│   │   │   ├── components/
│   │   │   ├── hooks/
│   │   │   ├── api.ts
│   │   │   └── types.ts
│   │   └── ...
│   ├── shared/
│   │   ├── components/
│   │   │   ├── ui/              # shadcn/ui (gerado — não editar convenções à mão, ver §17)
│   │   │   └── layout/          # AppLayout, Sidebar, Topbar
│   │   ├── hooks/
│   │   └── lib/                 # httpClient (axios), queryClient, utils
│   └── styles/ (index.css)      # Tailwind + variáveis de tema claro/escuro
└── tests/
```

Uma pasta `stores/` (Zustand) só é criada quando a primeira feature precisar de estado de cliente real de fato — não existe vazia hoje (`CLAUDE.md` §1.6). Componentes de layout hoje são vazios/placeholder até a Sprint 2 popular sidebar e topbar com dado real de workspace/usuário.

Nomenclatura e outras convenções detalhadas em `docs/10-coding-standards.md`.

---

## 14. Nomenclatura de arquivos

- Backend (Python): `snake_case.py`. Classes em `PascalCase`, funções/variáveis em `snake_case`, constantes em `UPPER_SNAKE_CASE`.
- Frontend (TypeScript): componentes em `PascalCase.tsx`, hooks em `useCamelCase.ts`, utilitários em `camelCase.ts`, tipos em `types.ts` por feature.
- Testes espelham o nome do arquivo testado com sufixo: `test_issue_service.py` / `IssueCard.test.tsx`.
- Nenhuma abreviação obscura (`svc`, `repo` como nome de variável são aceitos por serem convenção do próprio padrão arquitetural; evitar abreviações fora desse vocabulário já estabelecido).

---

## 15. Convenção de commits (Conventional Commits)

```
<tipo>(<escopo opcional>): <descrição no imperativo, em português ou inglês — manter consistência por PR>

[corpo opcional explicando o porquê]

[rodapé opcional: BREAKING CHANGE, refs a issue]
```

Tipos permitidos: `feat`, `fix`, `refactor`, `perf`, `test`, `docs`, `chore`, `build`, `ci`. Exemplo: `feat(issues): adiciona transição de status com validação de workflow`.

Regras: um commit = uma mudança logicamente coesa; `docs` para mudanças só em `docs/` ou `CLAUDE.md`; `BREAKING CHANGE:` no rodapé sempre que um contrato de API listado em `docs/04-api-design.md` mudar de forma incompatível.

---

## 16. Estratégia de testes

Pirâmide de testes, do mais barato/numeroso ao mais caro/escasso:

1. **Unitário (backend: services com repository fake; frontend: funções puras e hooks isolados)** — maioria dos testes, roda em milissegundos, sem I/O.
2. **Integração (backend: repository + banco de teste real via container efêmero; frontend: componentes com Testing Library + mock de rede via MSW)** — valida que a camada de acesso a dados e a camada de UI se comportam corretamente com dependências reais/realistas.
3. **Contrato de API (backend: rota completa via `AsyncClient` contra app real + banco de teste)** — garante que o contrato documentado em `docs/04-api-design.md` é o que de fato é servido.
4. **E2E (Playwright, um punhado de fluxos críticos: signup → criar workspace → criar issue → mudar status)** — não substitui as camadas anteriores; existe só para os fluxos que geram maior confiança de "o produto funciona".

Regras: toda regra de negócio nova exige teste unitário de service; toda rota nova exige ao menos um teste de contrato feliz + um de erro (403/404/422 conforme aplicável); cobertura não é meta em si — testar comportamento, não linha.

---

## 17. Regras de documentação

- Código não leva docstring/comentário explicando **o quê** (o nome já diz). Comentário só para **por quê** não-óbvio (uma regra de negócio estranha, um workaround de bug de biblioteca, um invariante escondido).
- Toda rota pública é autodocumentada via OpenAPI (FastAPI gera isso a partir dos schemas Pydantic e docstring curta do endpoint) — não há Swagger escrito manualmente em paralelo.
- Mudança de contrato de API deve ser refletida em `docs/04-api-design.md` no mesmo PR.
- Nova decisão arquitetural relevante (nova dependência, mudança de padrão) exige entrada em `docs/09-decision-log.md` no mesmo PR.

---

## 18. Checklist obrigatório antes de concluir qualquer tarefa

- [ ] O código segue o fluxo de camadas do §3 (router → service → repository), sem pular etapas?
- [ ] Toda query com escopo de tenant recebe e aplica `workspace_id` explicitamente?
- [ ] Autorização (RBAC) foi checada via `Depends(require_permission(...))`, não com `if` solto?
- [ ] Exceções lançadas são de domínio (`FlowDeskError` e subclasses), não `HTTPException` direto no service?
- [ ] Resposta segue o envelope padrão (`data`/`meta`/`error`) e usa `response_model` explícito?
- [ ] Testes cobrindo o caminho feliz e ao menos um caminho de erro relevante foram escritos e passam?
- [ ] Lint, format e type-check (`ruff`, `mypy` / `eslint`, `tsc`) rodam sem erro?
- [ ] Nenhum segredo, token completo ou dado sensível está sendo logado?
- [ ] `docs/04-api-design.md` e/ou `docs/03-database.md` foram atualizados se o contrato ou o schema mudou?
- [ ] O commit segue Conventional Commits e está no escopo mínimo necessário?
