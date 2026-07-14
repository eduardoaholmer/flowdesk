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
