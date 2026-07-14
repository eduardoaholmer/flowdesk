# 09 — Registro de Decisões Arquiteturais (ADR)

Formato: contexto, problema, alternativas consideradas, decisão, vantagens, desvantagens, impacto futuro. Uma ADR nunca é editada retroativamente para "parecer certa depois do fato" — se uma decisão for revertida, uma nova ADR é criada referenciando a anterior como superada.

---

## ADR-001 — Backend em Python/FastAPI em vez de stack 100% TypeScript

**Contexto**: o frontend já é TypeScript (React). Manter o backend também em TypeScript (ex.: NestJS) unificaria o monorepo em uma única linguagem, permitindo compartilhar tipos entre cliente e servidor sem geração de código.

**Problema**: qual linguagem/framework de backend maximiza tanto a qualidade técnica do sistema quanto o valor do projeto como portfólio?

**Alternativas consideradas**:
- **NestJS (TypeScript)**: unifica linguagem, compartilhamento de tipos trivial, DI nativo similar ao Spring/Angular.
- **Django + DRF (Python)**: extremamente produtivo para CRUD, admin panel gratuito, ORM síncrono maduro.
- **FastAPI (Python)**: async nativo, validação via Pydantic integrada ao próprio sistema de tipos, geração automática de OpenAPI, DI simples via `Depends`.

**Decisão**: FastAPI (Python 3.12).

**Vantagens**:
- Demonstra competência em dois ecossistemas de produção distintos (valor de portfólio explícito — ver `docs/00-product-vision.md` §2) em vez de um único ecossistema JS/TS ponta a ponta.
- Pydantic v2 dá validação de schema e serialização com desempenho e ergonomia de tipagem comparáveis ao TypeScript, sem sacrificar a produtividade de Python.
- Assíncrono nativo (`async/await` sobre `asyncio`) sem a camada de abstração adicional que Django exige para o mesmo (Django Channels/ASGI é mais recente e menos idiomático que FastAPI, que nasceu async).
- Geração automática de documentação OpenAPI a partir dos mesmos schemas usados para validação — sem duplicação de contrato.

**Desvantagens**:
- Dois toolchains (Poetry + pnpm), duas configurações de lint/format/CI, curva de contexto ao alternar entre os dois códigos-fonte.
- Sem compartilhamento automático de tipos entre backend e frontend — o contrato de API (`docs/04-api-design.md`) precisa ser mantido consistente manualmente (mitigado por ele ser a fonte de verdade documentada antes da implementação, e por testes de contrato no backend).
- Nest teria DI mais estruturado "de fábrica"; recriamos um padrão de camadas equivalente manualmente em FastAPI (aceito — ver `CLAUDE.md` §3, o padrão é simples o suficiente para não precisar de um framework de DI dedicado).

**Impacto futuro**: caso o projeto precise de tipos compartilhados de forma mais rígida no futuro, a opção é gerar um cliente TypeScript a partir do schema OpenAPI (`openapi-typescript`) — decisão adiada até haver dor real de divergência de contrato, não implementada preventivamente.

---

## ADR-002 — Monorepo com aplicações desacopladas (API + SPA) em vez de monólito full-stack

**Contexto**: frameworks como Next.js permitem servir frontend e backend (API routes/Server Actions) a partir de um único processo/deploy.

**Problema**: acoplar as duas camadas em um único framework simplifica deploy, mas o projeto quer demonstrar uma API REST como contrato de primeira classe (valioso para portfólio: mostra desenho de API independente de um framework específico de frontend).

**Alternativas consideradas**:
- **Monólito full-stack (Next.js API routes)**: um único deploy, sem CORS a configurar, roteamento de API e UI juntos.
- **Dois serviços desacoplados, comunicando via REST/JSON**: contrato explícito, cada camada testável e deployável independentemente.

**Decisão**: dois serviços desacoplados (`backend/`, `frontend/`) dentro de um monorepo (facilita navegação e PRs que tocam ambos quando necessário, sem acoplar build/deploy).

**Vantagens**: a API é utilizável por qualquer cliente futuro (mobile, CLI, integração de terceiros) sem refatoração; o contrato de API é uma superfície de design deliberada e documentada (`docs/04-api-design.md`), não um acidente da forma como o framework de frontend estrutura rotas; cada aplicação escala e é deployada independentemente.

**Desvantagens**: CORS precisa ser configurado corretamente (`docs/07-security.md` §5); dois processos rodando em desenvolvimento (mitigado por Docker Compose, Sprint 1); sem geração de tipos client-side automática de um monólito TS.

**Impacto futuro**: novos clientes (app mobile, por exemplo) consomem a mesma API sem exigir mudança de arquitetura — este é o principal payoff de longo prazo da decisão.

---

## ADR-003 — SPA (Vite) em vez de Next.js para o frontend

**Contexto**: Next.js (App Router) é hoje a escolha default de mercado para aplicações React, incluindo suporte forte a SSR/RSC e deploy simplificado em plataformas como Vercel.

**Problema**: FlowDesk é uma aplicação quase inteiramente atrás de autenticação (dashboard de trabalho, não conteúdo público indexável) — os dois principais benefícios de SSR (SEO e first-paint de conteúdo público) não se aplicam à maior parte das telas do produto.

**Alternativas consideradas**:
- **Next.js (App Router, RSC)**: SSR/streaming, roteamento de arquivo, ecossistema Vercel.
- **React + Vite (SPA pura)**: build mais simples, sem conceitos de servidor (RSC, hidratação) para uma aplicação que não precisa deles.

**Decisão**: React + Vite como SPA.

**Vantagens**: modelo mental mais simples (um único ambiente de execução — o navegador — em vez de código que roda ora no servidor ora no cliente); nenhuma complexidade de hidratação/RSC para depurar; tempo de build e HMR mais rápidos para o tamanho deste projeto; combina naturalmente com a decisão de manter o backend como API separada (ADR-002) — um SSR em Next.js faria pouco sentido chamando uma API externa em vez de acessar o banco diretamente.
Este ponto é a demonstração deliberada de "não escolher por popularidade": Next.js é hoje a escolha mais promovida no ecossistema React, mas o valor de SSR não se aplica ao formato deste produto — adotá-lo mesmo assim seria complexidade sem benefício líquido, o oposto do princípio em `CLAUDE.md` §1.5.

**Desvantagens**: sem SSR, a página de login tem um first-paint ligeiramente mais lento (bundle JS precisa carregar antes de renderizar) — aceitável dado que não é conteúdo público otimizado para SEO; perde acesso a otimizações automáticas de imagem/font do Next.js (irrelevante para um dashboard de texto/dados, não um site de conteúdo visual).

**Impacto futuro**: se uma futura página pública de marketing (landing page) for necessária, ela pode viver como um app estático separado (ou mesmo em Next.js isolado) sem forçar a aplicação autenticada inteira a herdar a complexidade de SSR só por causa de uma página.

**Adendo (Sprint 1.5)**: o scaffold inicial via Vite instalou React 19 (não React 18, como registrado originalmente aqui e em `CLAUDE.md` §2). React 19 é estável, retrocompatível para o shell de componentes já existente, e a decisão de SPA acima independe da versão exata do React — não há motivo para downgrade só para casar com o texto original. `CLAUDE.md` §2 e `docs/05-frontend.md` foram atualizados para refletir React 19 como a versão vigente.

---

## ADR-004 — TanStack Query + Zustand em vez de Redux Toolkit único

**Contexto**: Redux (com RTK Query) resolveria tanto estado de servidor quanto de cliente em uma única biblioteca/paradigma.

**Problema**: qual abordagem de estado minimiza a classe de bug mais comum em dashboards React — dado de servidor cacheado manualmente ficando dessincronizado da fonte de verdade (o backend)?

**Alternativas consideradas**:
- **Redux Toolkit + RTK Query**: uma biblioteca, um paradigma, ecossistema maduro de DevTools.
- **TanStack Query (estado de servidor) + Zustand (estado de cliente)**: bibliotecas especializadas, cada uma resolvendo exatamente um tipo de estado.

**Decisão**: TanStack Query + Zustand, com fronteira estrita entre os dois tipos de estado (`docs/05-frontend.md` §4).

**Vantagens**: TanStack Query resolve nativamente cache, invalidação, refetch em foco de janela, mutations otimistas e deduplicação de requisição — tudo que RTK Query também oferece, mas com API mais direta para este caso de uso específico; Zustand para estado de UI puro é drasticamente mais simples que reducers/actions/slices do Redux para o volume pequeno de estado de cliente que este produto realmente tem (sidebar, tema, filtros em edição).

**Desvantagens**: duas bibliotecas em vez de uma; exige disciplina de equipe para não vazar estado de servidor para dentro de um store Zustand "por conveniência" (mitigado como regra explícita em `CLAUDE.md`/`docs/05-frontend.md`).

**Impacto futuro**: se o estado de cliente crescer muito em complexidade (máquinas de estado elaboradas), Zustand pode ser complementado por XState sem afetar a camada de estado de servidor, que permanece intocada.

---

## ADR-005 — JWT + Refresh Token rotativo em vez de sessão pura em servidor

**Contexto**: autenticação via sessão de servidor (cookie de sessão + store em Redis) é uma alternativa igualmente válida e mais simples de revogar instantaneamente.

**Problema**: qual modelo de autenticação equilibra escalabilidade stateless, revogação e superfície de ataque, e ao mesmo tempo demonstra um padrão amplamente usado em APIs públicas modernas?

**Alternativas consideradas**:
- **Sessão de servidor** (cookie opaco + estado em Redis): revogação instantânea trivial (apagar a sessão), mas exige consulta a Redis em toda requisição autenticada.
- **JWT stateless puro (sem refresh)**: sem consulta a store em toda requisição, mas token de vida longa é perigoso (não revogável antes de expirar) e token de vida curta sem refresh forçaria login frequente.
- **JWT de vida curta + Refresh Token rotativo opaco**: combina baixa latência (JWT não exige lookup para a maioria das requisições) com revogabilidade real (refresh token é checado contra o banco, pode ser invalidado).

**Decisão**: JWT (access, 15 min) + refresh token rotativo opaco em cookie HttpOnly (30 dias), detalhado em `docs/07-security.md`.

**Vantagens**: a maioria das requisições (autenticadas via access token) não exige round-trip a banco/Redis para validar sessão — apenas verificação de assinatura; revogação continua possível via o refresh token (que é checado contra o banco) — comprometimento é contido à janela de 15 minutos do access token vazado; rotação com detecção de reuso mitiga roubo de refresh token de longa duração.

**Desvantagens**: mais complexo de implementar corretamente que sessão pura (rotação, detecção de reuso, dois artefatos de token em vez de um); um access token comprometido não pode ser revogado instantaneamente sem uma blocklist adicional (mitigado com blocklist pontual via `jti` em Redis para o caso excepcional, `docs/07-security.md` §1).

**Impacto futuro**: se o produto crescer para múltiplos serviços de backend, chaves assimétricas (`RS256`) já usadas permitem que outros serviços validem o access token com a chave pública sem acesso ao segredo de assinatura — decisão já tomada pensando nesse crescimento (`docs/06-backend.md` §7).

---

## ADR-006 — PostgreSQL em vez de banco não-relacional

**Contexto**: bancos orientados a documento (MongoDB) são por vezes escolhidos por "flexibilidade de schema" em produtos em estágio inicial.

**Problema**: o domínio de FlowDesk (workspace → time → issue → comentário/label, com relacionamentos N:N como issue↔label e projeto↔time) é fundamentalmente relacional; qual banco representa isso com menor esforço e maior garantia de integridade?

**Alternativas consideradas**:
- **MongoDB**: schema flexível, sem necessidade de migrations formais, bom para dado fracamente estruturado.
- **PostgreSQL**: relacional, transações ACID completas, constraints declarativas, JSONB disponível para os poucos campos que de fato se beneficiam de schema flexível (`notifications.payload`).

**Decisão**: PostgreSQL 16.

**Vantagens**: FKs e constraints (`UNIQUE (team_id, number)`, `UNIQUE (workspace_id, slug)`) garantidas pelo banco, não reimplementadas em código de aplicação; transações reais permitem que "mudar status + registrar atividade" seja atômico via Unit of Work; JSONB cobre o caso pontual de dado semiestruturado (`notifications.payload`) sem exigir um segundo banco; full-text search nativo (`tsvector`/GIN) cobre RF-ISSUE-09 sem dependência externa (Elasticsearch) no MVP.

**Desvantagens**: schema exige migration formal para evoluir (aceito como benefício, não custo — força pensar em compatibilidade, ver *expand/backfill/contract* em `docs/03-database.md` §10); sharding horizontal é mais trabalhoso que em bancos document-oriented nativamente distribuídos (irrelevante na escala deste projeto; se necessário no futuro, particionamento por `workspace_id` é o caminho natural, dado que já é a chave de isolamento de tenant em toda tabela).

**Impacto futuro**: a coluna `workspace_id` denormalizada em praticamente toda tabela (`docs/03-database.md` §4), decidida por motivo de segurança/isolamento, é também exatamente a chave de partição que seria usada em um particionamento futuro por tenant — as duas decisões se reforçam.

---

## ADR-007 — Desvios da modelagem de domínio da Sprint 2 em relação ao ER original da Sprint 0

**Contexto**: a Sprint 2 modelou o domínio completo (models, repositories, migrations). O pedido original da sprint listava 14 entidades sem `Team`/`WorkflowState` (que `docs/00-product-vision.md` e `docs/01-requirements.md` marcam como `[MVP]`) e incluindo `Project` (marcado como pós-MVP nesses mesmos documentos) — uma divergência resolvida com o usuário antes de implementar (ver histórico da sprint).

**Decisão 1 — incluir `Team`, `TeamMember`, `WorkflowState`, `TeamIssueCounter`**: RF-TEAM-01/02/03 e RF-ISSUE-02/03/05 são `[MVP]` e dependem estruturalmente dessas entidades (uma issue sem time não tem workflow nem numeração `ENG-123`). `TeamIssueCounter` não é uma entidade nova de fato — já estava prevista em prosa em `docs/03-database.md` §8 ("tabela de contador com `SELECT ... FOR UPDATE`"), só faltava ser criada.

**Decisão 2 — manter `Project` no escopo, sem `Cycle` nem o join `Project ↔ Team`**: pedido explícito do usuário. O *schema* de `Project` existe desde já; a *feature* (endpoints, regra de negócio) continua pós-MVP conforme `docs/00-product-vision.md` §5 — modelar o schema adiantado não implementa a funcionalidade, só evita uma migração de "adicionar tabela" isolada quando a feature chegar. `Cycle` e o relacionamento N:N `Project ↔ Team` ficam de fora até então.

**Decisão 3 — `Session` como entidade nova entre `User` e `RefreshToken`**: o ER original da Sprint 0 tinha `RefreshToken` pendurado direto em `User`. O pedido da Sprint 2 introduziu `Session` como entidade própria. Em vez de tratá-la como redundante, ela virou o nível certo para "dispositivos/logins ativos": `Session` guarda `user_agent`/`ip_address`/`last_seen_at`/`revoked_at`; `RefreshToken` (o segredo rotativo de `docs/07-security.md` §2) passou a referenciar `session_id`. Revogar uma sessão (logout) revoga junto seu token ativo — um único ponto de controle em vez de dois. Isso também abre caminho natural para uma futura tela "seus dispositivos conectados" sem mudança de schema.

**Decisão 4 — `Invitation` ganhou soft delete**: não estava no ER original (só tinha `expires_at`/`accepted_at`). Adicionado para permitir cancelar um convite pendente sem apagar o histórico de quem convidou quem, consistente com o resto do domínio.

**Decisão 5 — `Attachment` como associação polimórfica simples**: nova entidade (`docs/00-product-vision.md` já listava anexos como pós-MVP). Modelada com `issue_id`/`comment_id` nullable + `CHECK (num_nonnulls(issue_id, comment_id) = 1)` em vez de uma tabela `attachable` genérica — o domínio só tem dois tipos-alvo possíveis hoje, uma abstração polimórfica mais elaborada seria especulativa (`CLAUDE.md` §1.6).

**Impacto futuro**: `Cycle`, o join `Project ↔ Team` e o papel `GUEST` completo continuam como próximos candidatos naturais de expansão de schema quando suas sprints chegarem (`docs/08-roadmap.md`), sem exigir revisão do que já foi construído aqui.

---

## ADR-008 — Sprint 3 (Identidade e Autenticação): escopo e desvios de implementação

**Contexto**: a Sprint 3 implementou o sistema completo de autenticação (`AuthService`, `core/security.py`, `core/dependencies.py`, rate limiting). O pedido da sprint divergia em alguns pontos do contrato originalmente esboçado em `docs/04-api-design.md` §2 e do escopo de `docs/08-roadmap.md` (que incluía Workspaces). Cada divergência abaixo foi uma decisão deliberada, não um desvio acidental.

**Decisão 1 — Escopo da sprint é só autenticação, sem Workspaces**: `docs/08-roadmap.md` original incluía RF-WS-01–05/07 na Sprint 3. O pedido explícito do usuário para esta sprint excluiu Workspaces/Convites/RBAC/Projetos/Issues — mesmo padrão de resolução de divergência já usado na ADR-007 (pedido explícito do usuário prevalece sobre o roadmap anterior). Workspaces fica para a Sprint 4.

**Decisão 2 — `GET /users/me` em vez de `GET /auth/me`, sem lista de workspaces**: a sprint pediu esse endpoint e path explicitamente. Como é um recurso (o usuário), não uma ação de autenticação, ganhou uma feature própria (`features/users/`) reaproveitando `UserRepository` do auth. A resposta não inclui workspaces (não implementados ainda nesta sprint) — volta na Sprint 4, quando `WorkspaceMember` tiver uma API própria.

**Decisão 3 — `POST /auth/logout-all` adicionado ao contrato**: não estava em `docs/04-api-design.md` original; a sprint pediu "encerrar todas as sessões do usuário" explicitamente. Revoga toda sessão ativa de `SessionRepository.list_active_by_user`, uma por uma, na mesma unidade de trabalho.

**Decisão 4 — Mitigação de timing side-channel no login**: sem cuidado extra, "e-mail inexistente" responde muito mais rápido que "senha errada" (que roda Argon2id), vazando por tempo de resposta a mesma informação que `invalid_credentials` genérico tenta esconder. Quando o e-mail não existe, o login roda `perform_dummy_verification` (Argon2id contra um hash fixo, nunca uma senha real) antes de recusar — iguala o tempo dos dois caminhos.

**Decisão 5 — Blocklist de `jti` adiada**: `docs/07-security.md` §1 descreve o blocklist de access token em Redis como mecanismo para o caso raro de revogação pontual antes da expiração, não como parte do fluxo padrão de logout. Implementá-lo agora exigiria um round-trip a Redis em toda requisição autenticada sem necessidade comprovada nesta sprint — logout/logout-all já revogam a sessão e o refresh token, e o access token remanescente expira sozinho em até 15 min (trade-off já aceito em ADR-005). Fica como melhoria futura.

**Decisão 6 — Falha de CSRF em `/auth/refresh` usa o mesmo código `invalid_refresh_token`**: em vez de um código dedicado (`csrf_token_invalid`), uma checagem de CSRF malsucedida devolve o mesmo 401 genérico de qualquer outra falha de refresh (token ausente/expirado/reusado). Não revela ao chamador qual das checagens falhou — mesmo racional anti-enumeration do `invalid_credentials`.

**Decisão 7 — Rate limit de `/auth/refresh` por hash do cookie, não por usuário**: o limite documentado em `docs/07-security.md` §6 como "por usuário" na prática usa o hash SHA-256 do próprio cookie `refresh_token` como chave (com IP como fallback se o cookie não vier) — a identidade do usuário só é conhecida depois de uma consulta ao banco, o que contradiz checar o rate limit *antes* de qualquer acesso a dado (`docs/06-backend.md` §5).

**Decisão 8 — Commit de transação: `FlowDeskError` commita, exceção não mapeada reverte**: `core/db.py::get_db_session` precisou de uma regra explícita de boundary transacional (nenhuma existia antes da Sprint 3, já que nenhuma rota anterior persistia escrita real via HTTP). Uma `FlowDeskError` é um resultado de negócio válido — pode carregar efeito colateral intencional que deve persistir mesmo quando a requisição termina em erro (ex.: `AuthService.refresh` detecta reuso, revoga a sessão inteira, *e então* lança `InvalidRefreshTokenError`; se essa exceção disparasse rollback, a revogação de defesa seria desfeita silenciosamente). Só uma exceção verdadeiramente inesperada (não mapeada) reverte a transação.

**Decisão 9 — Cliente Redis e engine do Postgres com escopo por event loop**: ambos eram singletons de módulo criados uma vez no import (`core/db.py`, `core/rate_limit.py`), o padrão usado desde a Sprint 2. Isso quebra sob `pytest-asyncio` (loop novo por função de teste) com `RuntimeError: Event loop is closed` na segunda função de teste que toca o recurso — só descoberto agora porque a Sprint 3 é a primeira a ter testes de contrato que de fato usam banco/Redis através da app real (testes de sistema anteriores só tocavam `/health`/`/version`). Corrigido recriando o cliente/engine quando o event loop corrente muda; em produção (um único loop pela vida do processo) o comportamento é idêntico a um singleton normal, sem custo extra.

**Impacto futuro**: a Sprint 4 (Workspaces) reintroduz o campo `workspaces` na resposta de `GET /users/me` e implementa RBAC sobre o que a Sprint 3 deixou pronto (`CurrentUser`, `get_current_user`, a estrutura de exceções). O blocklist de `jti` (Decisão 5) e a calibração fina dos parâmetros de custo do Argon2id (`docs/07-security.md` §7) continuam como melhorias de produção não bloqueantes.

---

## ADR-009 — Sprint 4 (Multi-Tenancy: Workspaces, Memberships e Convites): escopo e desvios de implementação

**Contexto**: a Sprint 4 implementou toda a infraestrutura de Workspaces, Memberships e Convites sobre o schema já modelado na Sprint 2 (`docs/03-database.md` §6) e o contrato de API já esboçado desde a Sprint 0 (`docs/04-api-design.md` §3). O pedido explícito do usuário para esta sprint mantém RBAC detalhado, Projetos, Issues e Dashboard fora do escopo — mesmo padrão de resolução de divergência entre pedido do usuário e planejamento anterior já usado nas ADR-007 e ADR-008. Cada divergência abaixo foi deliberada, não acidental.

**Decisão 1 — `WorkspaceActivityLog` é uma tabela nova, não uma generalização de `activity_logs`**: `activity_logs` (Sprint 2, `features/issues/models.py::ActivityLog`) tem `issue_id` `NOT NULL` e a forma `action`/`field`/`old_value`/`new_value` — um histórico de diff de campo de uma `Issue`, não um log de auditoria genérico. Tornar `issue_id` nullable e reaproveitar a tabela para eventos de workspace (criação, atualização, exclusão, convite enviado/aceito, saída de membro) exigiria uma tabela polimórfica só para caber um caso de uso que não é dela — contra "Fronteiras explícitas" (`CLAUDE.md` §1.3). Criada `workspace_activity_logs` (migration `c2792667d7f6`) com `metadata JSONB` (payload livre por evento) em vez de colunas fixas de diff, já que eventos de workspace não compartilham uma forma de "campo mudou de X para Y" única. Duas tabelas de auditoria distintas, cada uma com o formato que seu domínio realmente usa.

**Decisão 2 — Slug: opcional na criação (auto-gerado), validado e mutável no `PATCH`**: o pedido da sprint permitia slug "gerado automaticamente ou validado". Implementado `POST /workspaces` com `slug` opcional — se ausente, `_slugify(name)` (transliteração best-effort via `unicodedata`, sem dependência nova) gera um candidato, com fallback de sufixo aleatório (`secrets.token_hex(3)`) em caso de colisão (até 5 tentativas antes de `409 slug_taken`). Se o cliente enviar um slug explícito, ele nunca é mutado silenciosamente — colisão vira erro direto, não um "slug-2" surpresa. `PATCH` aceita `slug?` (o esboço de `docs/04-api-design.md` §3 já prescrevia isso) — reavalidado por formato e unicidade a cada mudança; não há restrição adicional de imutabilidade pós-criação nesta sprint.

**Decisão 3 — Não-membro recebe 404, membro com papel insuficiente recebe 403**: toda ação que opera sobre um `workspace_id` primeiro resolve a `WorkspaceMember` do chamador (`_require_member`, `features/workspaces/service.py`) — se ausente (workspace inexistente **ou** existente mas sem o chamador como membro), `WorkspaceNotFoundError` (404), nunca confirmando a existência do recurso a quem não participa (mesmo racional anti-enumeration de `invalid_credentials`/`invalid_token`, ADR-008). Só depois de confirmar a posse é que ações restritas (`OWNER`/`ADMIN`) checam papel via `_require_role`, retornando `PermissionDeniedError` (403). Isso ajustou o esboço original de `docs/04-api-design.md` §3, que listava 403 também para não-membro em alguns endpoints.

**Decisão 4 — Checagem de papel inline no service, sem `core/authorization.py`/`Depends(require_permission(...))`**: `CLAUDE.md` §10 e `docs/07-security.md` §8 descrevem o desenho-alvo (uma `PERMISSION_MATRIX` central + dependency de rota) — essa infraestrutura de RBAC é escopo explícito da Sprint 5 ("Ainda não implementar RBAC detalhado", pedido literal desta sprint). Implementadas duas funções puras (`_require_member`, `_require_role`) reaproveitadas por `WorkspaceService` e `InvitationService`, sem estado de protocolo HTTP — ponto de substituição único quando a matriz completa chegar, sem reescrever a checagem de posse (que já está correta e é o que garante isolamento, ver Decisão 3).

**Decisão 5 — `PATCH .../members/{member_id}` (alterar papel) e `DELETE .../members/{member_id}` (remover outro membro) não foram implementados**: ambos já constavam do esboço de `docs/04-api-design.md` §3 (Sprint 0), mas não estão na lista de funcionalidades explícitas desta sprint (que só pede criar/listar/alternar workspace, convidar, aceitar, **sair** de um workspace, e listar membros — nunca "remover outro membro" ou "promover/rebaixar"). Ambas dependem de uma checagem de papel mais fina que `_require_role` cobre mal sem virar RBAC de fato (ex.: "ADMIN pode alterar papel de MEMBER mas não de OWNER"). Adiadas para a Sprint 5, junto com `core/authorization.py`. `docs/04-api-design.md` §3 mantém as linhas originais, anotadas como pendentes.

**Decisão 6 — `POST /invitations/{token}/accept` é um router global, não aninhado sob `/workspaces/{workspace_id}`**: `CLAUDE.md` §4 exige recursos com escopo de tenant aninhados sob `/workspaces/{workspace_id}/...` — mas quem aceita um convite **ainda não é membro** do workspace, então não há como o cliente afirmar um `workspace_id` confiável na URL antes de aceitar, e o token opaco já resolve o workspace correto no servidor (exigir o ID também não agregaria segurança, só complicaria o link de convite). Mesmo racional já usado para `/auth/*` viver fora de `/users/{id}/...`. Implementado como um segundo `APIRouter` (`invitations_router`, prefixo `/invitations`) dentro do mesmo `features/workspaces/router.py` — mesmo módulo/service por já pertencer ao mesmo agregado de domínio (Invitation), rotas HTTP em prefixos distintos por essa assimetria de contexto de autenticação.

**Decisão 7 — Token de convite em texto plano só na resposta de criação**: sem infraestrutura de e-mail nesta sprint (fora do stack tecnológico definido, `CLAUDE.md` §2), o banco guarda só `token_hash` (SHA-256, mesmo padrão de `refresh_tokens` — novas funções `generate_invitation_token`/`hash_invitation_token` em `core/security.py`, espelhando as de refresh token sem reaproveitá-las diretamente, para não acoplar semânticas de expiração de domínios diferentes). O valor em texto plano é devolvido uma única vez em `POST .../invitations` (`InvitationCreatedResponse`) — depois disso é irrecuperável, e o `OWNER`/`ADMIN` precisa repassá-lo manualmente. Envio de e-mail transacional fica como melhoria futura de infraestrutura, não de domínio.

**Decisão 8 — Sem endpoint/estado de "workspace ativo"**: a sprint pediu para "preparar a infraestrutura" de alternância de workspace sem implementar RBAC. Decidido não introduzir nenhum estado de sessão de servidor nem header implícito (`CLAUDE.md` §4 já proíbe isolamento dependente de header implícito) — toda rota de recurso de tenant já recebe `workspace_id` explícito no path, e "alternar workspace" no cliente é simplesmente compor a próxima URL com outro `workspace_id`, com o service resolvendo posse a cada requisição (`docs/07-security.md` §9.1/§12). Não há nada de servidor para "preparar" além do que a checagem de posse (Decisão 3) já garante — a infraestrutura pedida já existe, é o padrão de rota em si.

**Decisão 9 — `status` de `WorkspaceMember` é um campo derivado fixo, não uma coluna nova**: o pedido descreve `Membership` com "usuário; workspace; role; data de entrada; status". Uma `WorkspaceMember` só existe (não soft-deletada) enquanto ativa — não há estado intermediário nesta sprint (convite pendente é `Invitation`, entidade separada, nunca uma membership em estado parcial). Em vez de uma coluna redundante com `deleted_at`, `WorkspaceMemberResponse.status` é computado como `"ACTIVE"` na camada de schema — não impede introduzir outros estados via coluna real se/quando o domínio pedir (ex.: `SUSPENDED`).

**Decisão 10 — Paginação offset-based genérica (`PaginationMeta`/`CollectionEnvelope`)**: `docs/04-api-design.md` §1 já definia offset-based para coleções pequenas e estáveis (`members`, `teams`) — implementado em `core/schemas.py` como par genérico reutilizável por qualquer feature futura com o mesmo perfil de coleção, em vez de recalcular `total_pages` ad-hoc em cada router.

**Impacto futuro**: a Sprint 5 (RBAC) implementa `core/authorization.py` (`can()`/`PERMISSION_MATRIX`/`Depends(require_permission(...))`), substitui `_require_role` sem alterar a checagem de posse (Decisão 3/4), e implementa `PATCH`/`DELETE .../members/{member_id}` (Decisão 5). Envio de e-mail transacional para convites (Decisão 7) e um mecanismo de transferência de propriedade de workspace (pré-requisito para um `OWNER` único sair sem bloqueio de `CannotLeaveAsSoleOwnerError`) continuam como melhorias futuras não bloqueantes.

---

## ADR-010 — Sprint 5 (RBAC): arquitetura de autorização e desvios de implementação

**Contexto**: a Sprint 5 implementou o sistema completo de autorização baseado em papéis, substituindo as duas funções puras que a Sprint 4 deixou como ponto de substituição único (`_require_member`/`_require_role`, `docs/09-decision-log.md` ADR-009 Decisão 4) por uma infraestrutura central (`core/permissions.py`, `core/authorization.py`) usada por toda rota de recurso de tenant. O pedido explícito da sprint mantém Projetos, Issues, Dashboard e Kanban fora do escopo — a matriz de permissões cobre esses domínios preventivamente (schema de permissão pronto, sem feature associada), mesmo padrão já usado para o schema de `Project` na Sprint 2 (ADR-007 Decisão 2).

**Decisão 1 — `core/authorization.py` importa `features.workspaces.{models,repository,exceptions}`, quebrando a regra geral de que `core/` é transversal e não depende de features**: toda decisão de permissão depende de resolver a associação do chamador com o workspace (`WorkspaceMember`, o tenant boundary do sistema) — sem isso, `PermissionService` não tem o que consultar. A alternativa (duplicar a resolução de posse em cada feature futura que precisar de RBAC — issues, comments, projects) é exatamente o tipo de reimplementação por rota que esta sprint elimina (pedido explícito: "nenhuma rota deverá verificar permissões diretamente"). Aceito como exceção deliberada e documentada, não como uma violação silenciosa do princípio de camadas do `CLAUDE.md` §3. Para não criar um import circular com `features/workspaces/dependencies.py` (que importa `PermissionService`/`get_permission_service` de `core/authorization.py` para montar `WorkspaceService`), `get_workspace_context` constrói `WorkspaceRepository` diretamente a partir da sessão em vez de depender da factory `get_workspace_repository`.

**Decisão 2 — `PermissionService.can`/`.require` recebem uma `WorkspaceMember` já resolvida, não `(user, workspace)` separados**: o pedido descreve `permission_service.can(user=..., workspace=..., permission=...)`. Como o sistema já modela "usuário associado a um workspace com um papel" como uma única entidade (`WorkspaceMember`), passar esse objeto resolvido é equivalente semanticamente e evita que `PermissionService` precise resolver a associação de novo — essa resolução já aconteceu na etapa "Workspace Context" (`get_workspace_context`), que a antecede no fluxo. `member.user_id`/`member.role` cobrem o que `user`/`workspace` separados dariam.

**Decisão 3 — Duas camadas de checagem de permissão, não uma só**: a maioria das ações é decidível só a partir do `workspace_id` do path (`Depends(require_permission(Permission.X))`, resolvido antes do service layer). Mas `member.update_role`/`member.remove` têm uma regra contextual ("ADMIN não gerencia OWNER") que depende do papel do **alvo** — só conhecido depois que o service busca a `WorkspaceMember` pelo `member_id`, também no path, mas cujo papel não é resolvível na etapa de Workspace Context (que só resolve a posse do *chamador*). Por isso `WorkspaceService.update_member_role`/`.remove_member` recebem `PermissionService` injetado e chamam `require_can_manage_member` explicitamente — o pedido da sprint já antecipava isso ("Service Layer" depois de "Permission Service" no fluxo, mas services também podem consultar `PermissionService` diretamente para checagens que dependem de um recurso já buscado). Nenhuma dessas duas chamadas reimplementa a regra: ambas vivem em `core/authorization.py`.

**Decisão 4 — Ownership override como um `frozenset` de permissões, não uma segunda matriz por recurso**: `issue.delete`/`comment.update`/`comment.delete` são concedidos a qualquer papel quando `resource_owner_id == member.user_id`, mesmo que a matriz base do papel não inclua a permissão (ex.: `MEMBER` não tem `issue.delete` no conjunto base, mas pode excluir a própria issue). Rejeitada a alternativa de uma segunda matriz `role -> permission -> "own only"/"any"` (mais expressiva, mas nenhuma linha real da matriz atual precisa de mais que "todo mundo com a permissão OU o dono", então a granularidade extra seria especulativa — `CLAUDE.md` §1.6).

**Decisão 5 — `PATCH`/`DELETE .../members/{member_id}` rejeitam alvo = o próprio chamador**: nem o pedido da sprint nem a matriz de `docs/07-security.md` §8 original cobriam esse caso. Decidido bloquear com `409 cannot_manage_own_membership` (não `403`, já que não é falta de permissão — é o endpoint errado para a intenção) em vez de permitir um `OWNER` se auto-remover ou se auto-rebaixar por esta rota, que pulparia a checagem de "não pode sair sendo o único OWNER" (`CannotLeaveAsSoleOwnerError`, ADR-009) já implementada em `.../members/me`. Preserva um único caminho para "sair"/"trocar meu próprio papel" em vez de dois com garantias diferentes.

**Decisão 6 — Promover a `OWNER` via `PATCH .../members/{member_id}` é sempre rejeitado (`422`, validação de schema, não autorização)**: transferência de propriedade de workspace continua fora de escopo (ADR-009, impacto futuro). Em vez de uma regra de autorização ("só um OWNER pode promover a OWNER", que ainda assim precisaria de um fluxo de aceite/confirmação para não ser uma escalação unilateral), `MemberUpdateRoleRequest` rejeita `role: "OWNER"` na validação Pydantic — mesmo padrão já usado por `InvitationCreateRequest` para convites (Sprint 4).

**Decisão 7 — Auditoria de acesso negado é um log estruturado (`WARNING`), não uma linha em `workspace_activity_logs`**: o pedido lista "tentativa de acesso negado (quando fizer sentido)" junto de eventos que já viram `WorkspaceActivityLog` (alteração de papel, remoção de membro). `workspace_activity_logs` é reservada a eventos de negócio bem-sucedidos (ADR-009 Decisão 1) — uma tentativa negada não é um evento de negócio, é um evento de segurança, e persistir toda tentativa negada em uma tabela visível a `OWNER`/`ADMIN` via API criaria uma superfície de enumeration nova (um usuário malicioso descobriria, pela ausência de uma entrada negada, comportamento do sistema). `PermissionService.require`/`.require_can_manage_member` emitem `structlog` no nível `WARNING` (`event="permission_denied"`) com contexto completo (`user_id`, `workspace_id`, `role`, `permission`) — suficiente para detecção de abuso via agregação de log (`CLAUDE.md` §9), sem expor um novo endpoint de auditoria.

**Decisão 8 — `member.role_changed`/`member.removed` são novos `action` em `WorkspaceActivityLog`, reaproveitando a tabela existente**: ao contrário da Decisão 7 (tentativa negada), uma troca de papel ou remoção bem-sucedida *é* um evento de negócio — mesmo padrão já usado por `workspace.updated`/`member.left` (ADR-009), sem exigir uma tabela nova.

**Impacto futuro**: quando Projetos/Issues/Comentários/Labels forem implementados (Sprint 6+), cada feature só precisa declarar `Depends(require_permission(Permission.ISSUE_CREATE))` na rota e, se a ação tiver uma regra de posse (ex.: excluir a própria issue), passar `resource_owner_id` ao chamar `PermissionService.can`/`.require` no service — nenhuma outra peça de `core/authorization.py` muda. Um mecanismo de transferência de propriedade de workspace (Decisão 6) e permissões customizadas por workspace (além dos quatro papéis fixos) continuam como possibilidades futuras não bloqueantes — ver `docs/08-roadmap.md`.

---

## ADR-011 — Sprint 6 (Núcleo de Projetos): escopo e desvios de implementação

**Contexto**: a Sprint 6 implementou a camada de service/router de Projetos (`features/projects/`) sobre o schema já modelado na Sprint 2 (ADR-007 Decisão 2), com RBAC completo já disponível desde a Sprint 5 (`Permission.PROJECT_*`, ADR-010) e sem nenhuma mudança de matriz de permissão necessária. O pedido da sprint incluiu redefinir o ciclo de vida de status do projeto e impedir exclusão quando há restrições — dois pontos que divergem do desenho especulativo original da Sprint 2. Cada decisão abaixo foi deliberada, não acidental.

**Decisão 1 — `ProjectStatus` redefinido de `PLANNED/IN_PROGRESS/COMPLETED/CANCELED` para `ACTIVE/ARCHIVED`**: o valor original foi modelado especulativamente na Sprint 2 (ADR-007 Decisão 2), antes de a feature ter contrato de negócio real. O que esta sprint pede é um ciclo de vida administrativo simples (arquivar/restaurar), não um workflow de progresso de execução — isso pertence a um futuro workflow por Issue (fora de escopo aqui; a distinção é a mesma que já justifica `workflow_states` existir para `Issue` e não para `Project`). Como a tabela `projects` nunca recebeu uma linha em produção (a feature existia só como schema+repository parciais) e a coluna `status` nunca teve `CHECK constraint` no banco (`domain_enum()` = `VARCHAR` sem constraint, `docs/03-database.md` §5), a redefinição foi uma mudança pura de `models.py` — migration `fc0a10c66145` não altera essa coluna.

**Decisão 2 — exclusão bloqueada por issues ativas, verificada via SQLAlchemy Core em vez do model ORM `Issue`**: o pedido da sprint ("impedir exclusão quando houver restrições") é o análogo, em nível de aplicação, da política já declarada na FK `issues.project_id -> projects.id` (`ON DELETE RESTRICT`) — mas soft delete não passa pelo `DELETE` físico que a FK protegeria, então a regra precisa ser reimplementada explicitamente no service (`ProjectHasActiveIssuesError`, 409). `ProjectRepository.has_active_issues()` consulta a tabela `issues` via `sqlalchemy.table()`/`column()` (SQLAlchemy Core), não via o model `Issue`: importar o model forçaria o SQLAlchemy a configurar seu grafo de mapeamento inteiro (incluindo a relação com `Comment`) como efeito colateral de só carregar `ProjectRepository`, o que quebra hoje porque `features/comments/` ainda não está registrada em `main.py`. Consultar por nome de tabela evita acoplar `features/projects/` ao estado de registro de outra feature só para uma checagem de existência.

**Decisão 3 — `project_activity_logs` como tabela própria, não reaproveitando `activity_logs`/`workspace_activity_logs`**: mesma decisão já tomada duas vezes (`ActivityLog` dedicada a `Issue` desde a Sprint 2; `WorkspaceActivityLog` criada na Sprint 4 em vez de generalizar `ActivityLog` — ADR-009 Decisão 1) aplicada pela terceira vez ao mesmo raciocínio: cada agregado audita no formato que seu domínio realmente usa (`metadata JSONB` livre por evento, como `WorkspaceActivityLog`, não o diff fixo `field`/`old_value`/`new_value` de `ActivityLog`) em vez de uma tabela polimórfica genérica — contra "Fronteiras explícitas" (`CLAUDE.md` §1.3). Migration `0aa72aead06a`.

**Decisão 4 — `db/models_registry.py`: correção de um bug latente de configuração de mapper cross-feature**: `Project.issues` (relationship por string para `"Issue"`, existente desde a Sprint 2) e `Issue.comments` (idem, para `"Comment"`) nunca haviam sido exercitadas ponta a ponta antes desta sprint — nenhum código anterior instanciava `Project`/`Issue` de fato. O SQLAlchemy só resolve relationships declaradas por string contra seu registry declarativo compartilhado depois que a classe alvo é importada em algum ponto do processo; `main.py` importava só os models alcançáveis a partir dos routers já registrados (auth/users/workspaces/projects), nunca Comments/Labels/Teams/Notifications/Attachments — qualquer instanciação de `Project`/`Issue` lançaria `sqlalchemy.exc.InvalidRequestError` na primeira configuração de mapper (`_check_configure()`). Corrigido extraindo a lista de imports que já existia em `db/migrations/env.py` (necessária para o autogenerate do Alembic) para um módulo próprio, `db/models_registry.py`, importado agora por ambos `env.py` e `main.py` — um único ponto de manutenção da lista (`CLAUDE.md` §1).

**Impacto futuro**: `Cycle` e o join `Project ↔ Team` continuam como próximos candidatos de expansão de schema (Sprint 8, `docs/08-roadmap.md`). O índice GIN de busca textual e um índice dedicado por `status` ficam como otimizações futuras não bloqueantes, só se o volume de projetos por workspace crescer além do esperado (`docs/03-database.md` §9) — deliberadamente não implementados agora.

---

## ADR-012 — Sprint 7 (Núcleo de Issues): desacoplamento de `Team`/`WorkflowState` e redesenho do schema

**Contexto**: o pedido explícito do usuário para esta sprint foi Issues escopadas a `workspace_id`/`project_id`, com identificador legível `FD-123`, status fixo (`Backlog/Todo/In Progress/In Review/Done/Canceled`) e campos `estimate`/`due_date` — nenhuma menção a `Team`. O schema modelado na Sprint 2 (ADR-007), porém, já continha `issues.team_id` (`NOT NULL`), `issues.status_id` (FK para `workflow_states`) e `number` único por `(team_id, number)` via `TeamIssueCounter`, com `features/issues/models.py`/`repository.py` já implementados sobre esse desenho (commit `09146f8`) e migrations já aplicadas (`e471449c3682`, `3bce4084eea4`, `74d9c63228bc`). `Team`/`TeamMember`/`WorkflowState` nunca ganharam service/router — existem só como schema dormant, nenhuma linha em produção. Mesmo padrão de divergência resolvido nas ADR-008/009/011: pedido explícito do usuário prevalece sobre o esboço original, registrado aqui.

**Problema**: como remover a dependência de `Team`/`WorkflowState` de `Issue` sem uma feature de Team/board configurável nesta sprint, mantendo identificador legível único e status extensível no futuro, e como isso deve ser refletido no schema já aplicado (não é mais um desenho em papel, é uma migration real).

**Alternativas consideradas**:
- **Implementar um CRUD mínimo de Team primeiro**: mais fiel ao desenho original (ADR-007), mas adiciona escopo não pedido nesta sprint (rotas/RBAC de Team) só para desbloquear Issues, e não produz o identificador `FD-123` do enunciado (produziria `ENG-123`).
- **Manter `team_id`/`status_id` nullable, ignorados pela regra de negócio**: evita a migration, mas deixa colunas mortas e uma FK obrigatória (`status_id NOT NULL`) sem preenchimento possível sem Team/WorkflowState — pior que removê-las, viola "Clareza sobre esperteza" (`CLAUDE.md` §1.1).
- **Redesenhar `Issue` sem `Team`, com status fixo e contador por workspace** (escolhida): atende ao pedido literal da sprint, mantém `Kanban`/`Cycles` (que dependem de agrupamento, não de `Team` per se) viáveis depois.

**Decisão 1 — remoção de `team_id`/`status_id`, ambos via migration destrutiva direta (sem *expand → backfill → contract*)**: como `issues` nunca recebeu linha em produção (nenhuma rota jamais existiu — mesma condição que já justificou a redefinição direta de `Project.status` na Sprint 6, ADR-011 Decisão 1), a migration nova (`down_revision` = `0aa72aead06a`) remove `team_id`/`status_id` e seus índices/FKs diretamente, sem passo de backfill. `status_id` (FK para `workflow_states`) é substituído por `status: IssueStatus` (`domain_enum`, mesmo padrão VARCHAR+sem-CHECK-nativo de `priority`), com os 6 valores do enunciado. Nenhuma validação de transição de estado é imposta (qualquer status pode ir para qualquer status) — o enunciado desta sprint não pede uma máquina de estados, e impor uma sem um workflow configurável por time seria regra inventada sem requisito real (`CLAUDE.md` §1.6, YAGNI). "Preparar a arquitetura para status customizados futuramente" (pedido explícito do enunciado) é satisfeito por `status` já ser `domain_enum`/`VARCHAR` sem `CHECK` nativo — adicionar um valor é uma migration aditiva simples; migrar para uma tabela `WorkflowState`-like por workspace (em vez de por time) fica como evolução natural quando Kanban/board configurável for pedido (não implementado agora).

**Decisão 2 — identificador `FD-{number}` como `@property` computada, não coluna própria**: `number` (inteiro sequencial, agora único por `(workspace_id, number)` em vez de `(team_id, number)`, sem filtro parcial — mesmo racional de nunca reciclar número mesmo após soft delete) é a única coluna persistida; `identifier` é uma `@property` do model ORM (`f"FD-{self.number}"`), permitida por `CLAUDE.md` §3 ("Model... pode conter apenas comportamento trivial derivado de dados"). Evita duplicar dado (armazenar `identifier` como string geraria uma segunda fonte de verdade sujeita a divergir de `number`). O prefixo `"FD"` é uma constante fixa (não uma coluna nova em `Workspace`, ao contrário de `Team.key`): como cada identificador só precisa ser único *dentro* do workspace (nunca comparado entre workspaces na mesma tela), um prefixo por-workspace customizável é valor especulativo nesta sprint — fica como evolução futura direta (adicionar `Workspace.issue_prefix`, trocar a constante pela coluna) se o produto pedir.

**Decisão 3 — `WorkspaceIssueCounter` gerado sob demanda via `INSERT ... ON CONFLICT DO UPDATE ... RETURNING`, não `SELECT ... FOR UPDATE` sobre uma linha pré-criada**: `TeamIssueCounter` (`docs/03-database.md` §8) depende de `TeamRepository.create()` sempre inserir a linha do contador junto com o time — não há um evento equivalente de "workspace criado" que este sprint deveria tocar (fora de escopo alterar `WorkspaceService`). Em vez disso, `IssueRepository.next_number()` usa um `INSERT` idempotente com `ON CONFLICT (workspace_id) DO UPDATE SET next_number = next_number + 1 RETURNING next_number` do dialeto Postgres: cria a linha do contador na primeira issue do workspace e incrementa atomicamente nas seguintes, sem exigir um passo de seed prévio nem uma corrida de leitura-antes-de-escrita — mesma garantia de atomicidade do `SELECT ... FOR UPDATE`, sem a dependência de uma linha pré-existente.

**Decisão 4 — `estimate`/`due_date` adicionados como colunas simples**: `estimate` (inteiro nullable, pontos de esforço) e `due_date` (`date` nullable) são campos novos pedidos explicitamente pelo enunciado, ausentes do desenho original da Sprint 2. Adicionados nullable sem passo de backfill (coluna nova, sem dado legado).

**Decisão 5 — paginação por offset, não cursor**: o esboço original em `docs/04-api-design.md` §5 (pré-existente, nunca implementado) previa paginação cursor-based para Issues por volume esperado alto. Esta sprint usa `CollectionEnvelope`/`PaginationMeta` (offset, já existente em `core/schemas.py`, mesmo padrão de Projects/Members/Teams) em vez de introduzir um segundo envelope de paginação (cursor) sem volume real que o justifique agora (`CLAUDE.md` §1.6). Migrar para cursor-based fica documentado aqui como ponto de retomada caso o volume real de issues por workspace cresça o suficiente para tornar `OFFSET` custoso.

**Decisão 6 — exclusão de issue com posse (`issue.delete`)**: a Sprint 5 (ADR-010) já havia deixado `Permission.ISSUE_DELETE` em `OWNERSHIP_OVERRIDE_PERMISSIONS`, prevendo exatamente esta regra ("Criador ou ADMIN+"). Como essa checagem depende de `issue.creator_id` (só conhecido após buscar a issue), a rota de exclusão usa `Depends(require_permission(Permission.ISSUE_READ))` (garante ao menos membership do workspace) em vez de `Depends(require_permission(Permission.ISSUE_DELETE))` — a permissão de fato é resolvida dentro de `IssueService.delete()`, que chama `PermissionService.require(..., resource_owner_id=issue.creator_id)` depois de buscar a issue. Resolver a permissão de posse no router exigiria buscar a issue duas vezes (uma no `Depends`, outra no service) ou vazar a busca de recurso para a camada de dependency — o padrão já usado por `WorkspaceService.require_can_manage_member` (checagem contextual pós-fetch dentro do service, não no router) é reaproveitado aqui.

**Desvantagens aceitas**: a migration desta sprint é destrutiva sobre uma tabela já criada (não apenas aditiva como as anteriores) — aceitável só porque `issues` nunca teve linha real, e documentado explicitamente aqui para que uma auditoria futura entenda por que uma tabela da Sprint 2 mudou de forma incompatível na Sprint 7. `Team`/`WorkflowState`/`TeamIssueCounter` ficam sem nenhum consumidor até uma sprint de Kanban/board por time os retomar — não removidos (schema ainda modelado, sem custo de manutenção real em ficar ocioso).

**Impacto futuro**: quando Kanban/board configurável (`docs/08-roadmap.md`, pós-MVP) for de fato implementado, duas rotas de evolução ficam abertas sem exigir novo redesenho de `Issue`: (a) reintroduzir um agrupamento por time via um novo `team_id` nullable + join, sem tocar `status`/`number`; ou (b) evoluir `status` de enum fixo para uma tabela de estados configurável por workspace (mesmo papel de `WorkflowState`, mas por workspace em vez de por time, coerente com o resto desta sprint). Labels (`IssueLabel`, já modelada) e Comentários (`Comment`, já modelado) permanecem prontos para a Sprint 8 sem qualquer mudança adicional de schema — nenhum dos dois depende de `team_id`/`status_id`.

---

## ADR-013 — Sprint 8 (Comentários, Labels, Anexos): menções sem notificação, Label como recurso compartilhado, e ponto de extensão de storage

**Contexto**: o pedido explícito do usuário ao final da Sprint 7 apontou esta sprint para Comentários, Labels e Anexos — `Comment`, `Label` e `Attachment` já existiam como schema desde a Sprint 2 (`create_comments`/`create_labels`/`create_attachments`, `docs/03-database.md` §10), mas nenhum dos três tinha `service`/`router`/`schemas` até agora (mesmo padrão "schema dormant" já visto em `Team`/`WorkflowState`, ADR-012). Diferente da Sprint 7, nenhuma tabela precisou de alteração destrutiva — as três features só exigiram colunas/tabelas aditivas sobre o desenho já existente.

**Problema**: como implementar as três features seguindo o esqueleto padrão (`CLAUDE.md` §3) sem introduzir escopo não pedido — em particular, como resolver "menção a um usuário em um comentário" sem uma UI de autocomplete nem um sistema de notificação (nenhum dos dois existe ainda), como decidir se Label segue o mesmo modelo de posse de Comentário/Issue, e como desenhar o armazenamento de arquivo de forma que não amarre o domínio a disco local para sempre.

**Alternativas consideradas**:
- **Menção via UI de autocomplete (`@` abre um dropdown de membros, referência por `user_id`)**: mais robusto e é o padrão de produtos como Linear/GitHub, mas exige componente de rich text/autocomplete no frontend — escopo não pedido pelo enunciado desta sprint.
- **Menção via regex sobre o local-part do e-mail** (escolhida): `@joao.silva` casado contra `joao.silva@empresa.com` — sintaxe simples o suficiente para um `<textarea>` puro, sem exigir autocomplete nem alterar `CommentCreateRequest` para aceitar uma lista de `user_id`s à parte do texto.
- **`Label.update`/`.delete` com ownership override (só quem criou a label ou `ADMIN`+ edita/exclui)**: consistente com Comentário/Issue/Anexo, mas trata a label como recurso pessoal — não faz sentido de produto: uma label ("bug", "urgente") é vocabulário compartilhado do workspace, não de quem a criou primeiro.
- **`Label.update`/`.delete` só `ADMIN`+, sem exceção de posse** (escolhida): trata Label como recurso compartilhado do workspace — qualquer `MEMBER`/`GUEST` pode criar e usar labels, só `ADMIN`+ pode reorganizar o vocabulário compartilhado.
- **Acoplar `AttachmentService` a um SDK de storage específico (ex.: `boto3`/S3) desde já**: adiantaria a Sprint pós-MVP de blob storage gerenciado, mas exigiria credenciais/infra externa só para rodar este projeto localmente — custo desproporcional ao pedido literal da sprint ("permitir futura migração para S3 ou serviço equivalente", não "usar S3 agora").
- **`StorageProvider` como `Protocol` + `LocalStorageProvider` como única implementação** (escolhida): satisfaz o pedido de "arquitetura preparada" sem a dependência externa — trocar para S3 no futuro é implementar uma segunda classe que satisfaça o mesmo protocolo, sem tocar `AttachmentService`.

**Decisão 1 — sintaxe de menção `@local-part-do-e-mail`, detecção e armazenamento são o escopo desta sprint; envio de notificação não**: `CommentService._resolve_mentions` extrai tokens via regex (`@([A-Za-z0-9._%+-]+)`) do `body` e casa cada um contra o local-part (parte antes do `@`) do e-mail dos membros do workspace — não contra o nome de exibição, que tem espaço e não é único. `CommentMention` (nova tabela, `docs/03-database.md` §6.4) persiste o resultado, mas nenhum evento é disparado para um sistema de notificação (que não existe ainda, `docs/08-roadmap.md`) — a arquitetura fica "preparada" (tabela existe, resolução funciona, `mentioned_user_ids` já está no `CommentResponse`) para uma sprint futura de notificações consumir essas linhas sem alterar `Comment`/`CommentMention`.

**Decisão 2 — resolução de menção limitada aos primeiros 200 membros do workspace, uma única query**: `_resolve_mentions` chama `WorkspaceRepository.list_members(workspace_id, page=1, per_page=200)` uma vez por comentário criado/editado, nunca uma query por menção (evita N+1). Suficiente para a escala de um workspace de portfólio; um workspace real com milhares de membros exigiria trocar por uma busca indexada por local-part de e-mail — não implementado agora, YAGNI (`CLAUDE.md` §1.6).

**Decisão 3 — Comentários não têm timeline própria**: toda mutação de comentário (`comment.created`, `comment.updated`, `comment.deleted`) gera uma entrada em `ActivityLog` — a timeline da **Issue-mãe** (`issue_id` obrigatório em `ActivityLog`), não uma tabela `CommentActivityLog` própria. Diferente de `LabelActivityLog` (Decisão 5 abaixo), um comentário não existe fora do contexto de uma issue — sua auditoria pertencer à timeline da issue é o modelo mais direto, sem introduzir uma segunda tabela de auditoria para um evento que um usuário já espera ver junto do resto do histórico da issue.

**Decisão 4 — `labels.description` como coluna aditiva nullable, sem passo de backfill**: campo novo pedido pelo enunciado, ausente do desenho original da Sprint 2 (migration `a7c1d9f0b2e4`) — mesmo padrão de `issues.estimate`/`issues.due_date` na Sprint 7 (ADR-012, Decisão 4).

**Decisão 5 — `LabelActivityLog` como tabela própria, não reaproveitando `ActivityLog`**: eventos de ciclo de vida do próprio `Label` (`label.created`, `label.updated` com diff por campo, `label.deleted`) são workspace-scoped, não issue-scoped — `ActivityLog.issue_id` é obrigatório, então não serve. Mesmo racional já aplicado à criação de `WorkspaceActivityLog` (ADR-009, Decisão 1) e `ProjectActivityLog` (ADR-011): `metadata JSONB`, append-only, sem `updated_at`/soft delete. Quando um Label é *aplicado/removido de uma Issue* (não criado/editado/excluído), o evento (`label.added`/`label.removed`) vai para a `ActivityLog` da Issue, não para `LabelActivityLog` — são dois eventos de domínio diferentes (ciclo de vida do Label vs. associação Label↔Issue) que só coincidem por envolverem a mesma entidade.

**Decisão 6 — `label.update`/`label.delete` sem ownership override**: ao contrário de `comment.update`/`comment.delete`/`issue.delete`/`attachment.delete` (todos em `OWNERSHIP_OVERRIDE_PERMISSIONS`), editar/excluir uma label exige `ADMIN`+ incondicionalmente — quem criou a label não ganha direito extra sobre ela. `LabelService` reflete isso não recebendo `PermissionService` no `__init__` (mesmo racional de `ProjectService`, ADR-011): toda autorização é resolvida inteiramente por `Depends(require_permission(...))` no router, sem checagem contextual.

**Decisão 7 — `core/validators.py::validate_hex_color` extraída de `features/projects/schemas.py`**: `LabelCreateRequest`/`LabelUpdateRequest` precisam exatamente da mesma validação de cor hex que `Project` já tinha desde a Sprint 6 — mesmo racional já aplicado a `core/slug.py::validate_slug_format` (`CLAUDE.md` §1, reuso de regra sem duplicar).

**Decisão 8 — `attachments.storage_provider` `NOT NULL` direto, sem *expand → backfill → contract***: mesma justificativa de `projects.slug`/`created_by` na Sprint 6 (ADR-011) e `issues.estimate`/`.due_date` na Sprint 7: `attachments` nunca teve linha em produção (schema dormant desde a Sprint 2), então um `server_default` temporário seguido de sua remoção (migration `f42ae23f3ec0`) é suficiente — nenhum dado legado a migrar de fato.

**Decisão 9 — `StorageProvider` como `Protocol` (`core/storage.py`), `LocalStorageProvider` como única implementação**: `save`/`open`/`delete` operam sobre `storage_key` (ponteiro opaco, nunca um path absoluto vazado para fora da camada) — `LocalStorageProvider` grava em disco sob `Settings.upload_dir` (`var/uploads/`), com `storage_key` prefixado por um UUID (nunca o nome original do arquivo, evitando colisão e qualquer ambiguidade de path a partir de um nome de arquivo malicioso). `Attachment.storage_provider` registra qual implementação gravou cada linha, permitindo que dado antigo (`"local"`) e um provider futuro (`"s3"`) coexistam na mesma tabela sem migração retroativa quando/se o produto crescer além de um deploy single-instance.

**Decisão 10 — validação de upload por lista branca de `Content-Type`, não extensão de arquivo**: `Settings.allowed_upload_content_types` (imagens comuns, PDF, texto) e `Settings.max_upload_size_bytes` (10 MB) são checados em `AttachmentService._validate` antes de qualquer byte ser persistido — extensão de arquivo é trivialmente forjável (renomear `.exe` para `.png`), `Content-Type` declarado pelo cliente é a validação mínima aceitável nesta sprint (validação de magic bytes/assinatura binária fica como evolução futura se o produto precisar de garantia mais forte que a lista branca por header).

**Decisão 11 — Anexo só a Issue nesta sprint, não a Comentário**: `Attachment.comment_id` já modela um alvo alternativo (polimorfismo pré-existente desde a Sprint 2, `CHECK (num_nonnulls(issue_id, comment_id) = 1)`), mas só `POST .../issues/{issue_id}/attachments` foi pedido pelo enunciado — anexar diretamente a um comentário (ex.: arrastar uma imagem para dentro do composer) fica para quando o produto pedir, sem exigir mudança de schema (a coluna já existe).

**Decisão 12 — `attachment.delete` com ownership override (uploader ou `ADMIN`+)**: mesmo padrão de `comment.delete`/`issue.delete` — `Permission.ATTACHMENT_DELETE` em `OWNERSHIP_OVERRIDE_PERMISSIONS`, resolvido em `AttachmentService.delete` via `PermissionService.require(..., resource_owner_id=attachment.uploader_id)` depois do fetch, mesma razão de não poder ser expresso só pela matriz estática de papel (router usa a dependency mais fraca `Permission.ISSUE_READ`, garantindo só membership).

**Decisão 13 — download de anexo passa pelo `httpClient` autenticado no frontend, não por um link estático**: o access token só existe em memória no frontend (`CLAUDE.md` §11, nunca `localStorage`/cookie) — uma `<a href>` apontando direto para `GET .../attachments/{id}` não carregaria o header `Authorization`. `useDownloadAttachment` (`frontend/src/features/attachments/hooks.ts`) busca o arquivo como blob via `httpClient` e dispara o download client-side (`URL.createObjectURL` + clique programático em uma âncora temporária).

**Desvantagens aceitas**: nenhuma notificação é de fato enviada quando um usuário é mencionado (a tabela existe, o consumo não) — aceitável porque o enunciado desta sprint pediu detecção/armazenamento, não o sistema de notificação inteiro (fora de escopo, `docs/08-roadmap.md`). Não há editor de texto rico para comentários (`<textarea>` simples, sem markdown/preview) nem upload por arrastar-e-soltar (botão + `<input type="file">`) — ambos são refinamento de UX não pedido pelo enunciado. Anexar diretamente a um comentário permanece não implementado, apesar do schema já suportar.

**Impacto futuro**: uma sprint de notificações em tempo real consome `CommentMention` (join por `mentioned_user_id`) sem exigir mudança de schema. Trocar `LocalStorageProvider` por um provider `"s3"` é implementar uma nova classe satisfazendo `StorageProvider`, registrar em `core/storage.py::get_storage_provider`, sem tocar `AttachmentService`/`AttachmentRepository` — dado antigo com `storage_provider = "local"` continua servível pelo `LocalStorageProvider` enquanto novo dado usa `"s3"`, sem migração de arquivo retroativa obrigatória. Anexar a um comentário (em vez de só a uma issue) é aditivo puro no service (`upload_to_comment`, análogo a `upload_to_issue`) quando pedido.

---

## ADR-014 — Sprint 8.5 (Frontend Foundation & Design System Preparation): tokens como camada de referência, primeiro store de UI, e o que ficou deliberadamente fora

**Contexto**: pedido explícito do usuário para preparar a fundação do frontend (design system, layouts, providers, hooks, utils, skeletons, empty states, arquitetura de tema) antes de uma sprint futura de identidade visual e telas finais — sem tela final, sem regra de negócio nova, sem cor nova. Diferente das sprints anteriores, não há schema/endpoint envolvido; todas as decisões são de organização de código frontend.

**Decisão 1 — `shared/theme/tokens.ts` referencia tokens existentes, não inventa nenhum**: cores, radius, espaçamento e tipografia continuam vivendo em `src/index.css`/escala default do Tailwind — `tokens.ts` só documenta esse vocabulário para consumo tipado em TS. A única categoria genuinamente nova é motion (`--duration-*`/`--ease-*`, sem equivalente anterior no projeto), adicionada de forma aditiva em `src/index.css` sem tocar nenhuma cor. Detalhes em `docs/05-frontend.md` §9.

**Decisão 2 — `shared/stores/uiStore.ts` é o primeiro store Zustand de UI cliente-only**: guarda colapso da Sidebar e estado do menu mobile. `authStore.ts` já existia, mas guarda sessão (dado de segurança), não preferência de UI — a distinção importa porque `uiStore` pode crescer para outros estados efêmeros futuros (filtro em edição, etc.) sem reabrir essa decisão a cada novo caso.

**Decisão 3 — consolidação de `EmptyState`/Skeleton elimina duplicação real, não hipotética**: a auditoria inicial encontrou `IssuesEmptyState`/`ProjectsEmptyState` e `IssuesListSkeleton`/`ProjectsListSkeleton` estruturalmente idênticos entre si, copiados por feature — generalizados em `shared/components/EmptyState.tsx` (sobre o primitivo oficial `ui/empty.tsx`, instalado nesta sprint) e `shared/components/skeletons/ListSkeleton.tsx`; as versões por feature viraram wrappers finos com a cópia/ícone/ação específicos. Pelo mesmo critério, `formatDate`/`formatDateTime` (`shared/lib/date.ts`) e `getInitials` (`shared/lib/string.ts`) substituíram a mesma expressão duplicada em 5 componentes (`CommentItem`, `IssueActivityTimeline`, `IssueDetailView`, `IssuesTable`, `ProjectDetailView`).

**Decisão 4 — `AuthLayout`/`EmptyLayout` passam a existir; `WorkspaceLayout` continua não existindo**: `docs/05-frontend.md` §3 descrevia os três desde a Sprint 0 sem que os dois primeiros tivessem sido implementados de fato (divergência já sinalizada, mas não corrigida, pela nota da Sprint 7). Esta sprint implementa `AuthLayout`/`EmptyLayout` (extraindo a marcação já usada por `LoginPage`/`HomePage`, sem mudar comportamento) e corrige a documentação. `WorkspaceLayout` seguiu de fora: nenhuma página filha precisa hoje de mais contexto de workspace do que `useWorkspace`/`useCurrentUser` (TanStack Query) já resolvem — criá-lo agora seria generalidade especulativa (`CLAUDE.md` §1.6).

**Decisão 5 — seletor de workspace na Sidebar usa `profile.workspaces` real, não dado mockado**: o enunciado da sprint pedia "dados mockados" para a Sidebar; na prática, `useCurrentUser` já busca a lista de workspaces do usuário para outros fins (resolver `useWorkspace`, o próprio `Topbar` antigo) — reaproveitar esse dado real é menos código, não introduz chamada nova nem regra de negócio (é navegação entre slugs já carregados), e evita um dado fake divergindo da sessão real. Decisão confirmada com o usuário antes da implementação.

**Decisão 6 — `features/teams/` deliberadamente não criado**: o enunciado da sprint listava `teams/` entre as features a estruturar, mas a ADR-012 (Sprint 7) removeu `Team` do domínio (issues/projetos não referenciam mais time). Recriar a pasta reintroduziria um conceito descartado sem que exista entidade de domínio por trás. Confirmado com o usuário; `features/dashboard/` e `features/settings/` foram criados como placeholders documentados (nenhum dos dois foi removido de propósito em alguma sprint anterior).

**Decisão 7 — `field` instalado no lugar de `form`**: o registry shadcn/ui na versão atual (`style: radix-nova`) mantém `form` só como alias vazio (sem `files`) — o primitivo real de composição para `react-hook-form` nessa geração é `field` (`Field`/`FieldLabel`/`FieldError`/...), que já reflete o mesmo padrão manual (register + exibição de erro) usado em `CreateLabelDialog`/`LabelFormFields`. Descoberto ao rodar `npx shadcn add form` sem efeito nenhum; confirmado via `npx shadcn view @shadcn/form`.

**Desvantagens aceitas**: busca (Topbar) e notificações permanecem sem integração — UI presente, sem dado real, porque nenhuma das duas tem feature/endpoint por trás ainda (busca nunca teve endpoint; notificações são Sprint 9). Breadcrumb é estrutural (nome do workspace + seção da rota), não resolve título de issue/projeto individual — exigiria fetch adicional fora do escopo desta sprint.

**Impacto futuro**: a sprint de identidade visual pode estilizar diretamente sobre o que já existe (tokens, layouts, Sidebar/Topbar, skeletons, empty states) sem refatoração estrutural. Quando busca/notificações ganharem endpoint real, `TopbarSearch`/`TopbarNotifications` (`shared/components/layout/Topbar.tsx`) são os pontos de extensão já identificados.
