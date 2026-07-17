# 01 — Requisitos

Convenção: requisitos funcionais usam prefixo `RF`, não funcionais `RNF`. Cada um é rastreável a uma sprint em `docs/08-roadmap.md`. `[MVP]` indica que é obrigatório para o corte descrito em `docs/00-product-vision.md`.

> **Nota (pós-implementação, ADR-020)**: RF-TEAM-01/02/03 e RF-ISSUE-04/05/07 abaixo descrevem `Team` com workflow de status configurável — removido do domínio na Sprint 7 (ADR-012, `docs/09-decision-log.md`) em favor de `Issue` pertencendo diretamente a um workspace, com status como enum fixo (não configurável por time). RF-ISSUE-07 (board por status) nunca foi implementado como board de fato — é hoje o Milestone 5 (Kanban) do roadmap executivo, não mais `[MVP]`. Os requisitos abaixo permanecem como registro do pedido original (Sprint 0); o que de fato existe está em `docs/03-database.md`/`docs/04-api-design.md`, e o que ainda será construído está em `docs/08-roadmap.md`.

## 1. Requisitos Funcionais

### Autenticação e Conta (RF-AUTH)

- **RF-AUTH-01** [MVP] O sistema deve permitir cadastro de usuário com nome, e-mail e senha.
- **RF-AUTH-02** [MVP] O sistema deve validar unicidade de e-mail no cadastro.
- **RF-AUTH-03** [MVP] O sistema deve permitir login com e-mail/senha, emitindo access token (JWT) e refresh token (cookie HttpOnly).
- **RF-AUTH-04** [MVP] O sistema deve permitir logout, revogando o refresh token no servidor.
- **RF-AUTH-05** [MVP] O sistema deve permitir renovação de access token via refresh token válido.
- **RF-AUTH-06** O sistema deve permitir recuperação de senha via e-mail (token de reset com expiração). *(pós-MVP)*
- **RF-AUTH-07** [MVP] O sistema deve impedir login após N tentativas falhas em uma janela de tempo (rate limiting).

### Workspaces (RF-WS)

- **RF-WS-01** [MVP] O sistema deve permitir criação de um workspace, tornando o criador automaticamente `OWNER`.
- **RF-WS-02** [MVP] O sistema deve permitir convite de novos membros a um workspace por e-mail, com papel atribuído no convite.
- **RF-WS-03** [MVP] O sistema deve permitir que um `OWNER`/`ADMIN` altere o papel de um membro existente.
- **RF-WS-04** [MVP] O sistema deve permitir remoção de um membro do workspace por `OWNER`/`ADMIN`.
- **RF-WS-05** [MVP] Um usuário deve poder pertencer a múltiplos workspaces e alternar entre eles.
- **RF-WS-06** Um workspace deve poder ser renomeado e ter sua URL/slug alterada por `OWNER`.
- **RF-WS-07** [MVP] Dados de um workspace nunca devem ser visíveis ou acessíveis a partir de outro workspace, independentemente do papel do usuário.

### Times (RF-TEAM)

- **RF-TEAM-01** [MVP] O sistema deve permitir criação de times dentro de um workspace.
- **RF-TEAM-02** [MVP] Um time deve ter um workflow de status configurável (conjunto de estados e sua ordem), com um conjunto default ao ser criado.
- **RF-TEAM-03** [MVP] O sistema deve permitir adicionar/remover membros do workspace a um time.

### Issues (RF-ISSUE)

- **RF-ISSUE-01** [MVP] O sistema deve permitir criação de issue com título (obrigatório), descrição, status, prioridade, responsável e labels.
- **RF-ISSUE-02** [MVP] Toda issue deve pertencer a exatamente um time.
- **RF-ISSUE-03** [MVP] O sistema deve gerar um identificador legível por issue (ex.: `ENG-123`), único por time.
- **RF-ISSUE-04** [MVP] O sistema deve permitir alterar status, prioridade, responsável e labels de uma issue existente.
- **RF-ISSUE-05** [MVP] Transição de status deve respeitar o workflow configurado do time (não é permitido setar um status que não existe no workflow do time da issue).
- **RF-ISSUE-06** [MVP] O sistema deve permitir exclusão (soft delete) de issues por usuários com permissão adequada.
- **RF-ISSUE-07** [MVP] O sistema deve listar issues de um time em formato de board agrupado por status.
- **RF-ISSUE-08** [MVP] O sistema deve permitir filtrar issues por status, responsável, label e prioridade, combináveis.
- **RF-ISSUE-09** [MVP] O sistema deve permitir busca textual por título/descrição de issue dentro do workspace.
- **RF-ISSUE-10** O sistema deve registrar todo evento relevante da issue (criação, mudança de campo) em um log de atividade visível no detalhe da issue.

### Comentários (RF-COMMENT)

- **RF-COMMENT-01** [MVP] O sistema deve permitir adicionar comentários (markdown) a uma issue.
- **RF-COMMENT-02** [MVP] O sistema deve permitir editar/excluir um comentário próprio; `ADMIN`/`OWNER` podem excluir qualquer comentário do workspace.
- **RF-COMMENT-03** O sistema deve suportar menção a outro membro do workspace via `@usuário` dentro de um comentário.

### Projetos e Ciclos (RF-PROJ / RF-CYCLE) — pós-MVP

- **RF-PROJ-01** O sistema deve permitir agrupar issues de um ou mais times sob um projeto, com data alvo e status de progresso.
- **RF-CYCLE-01** O sistema deve permitir definir ciclos (janelas de tempo) por time e alocar issues a um ciclo.
- **RF-CYCLE-02** O sistema deve calcular e exibir progresso de um ciclo (issues concluídas vs. total, burndown simples).

### Notificações (RF-NOTIF) — pós-MVP

- **RF-NOTIF-01** O sistema deve notificar um usuário quando ele for mencionado em um comentário.
- **RF-NOTIF-02** O sistema deve notificar um usuário quando uma issue sob sua responsabilidade mudar de status.

## 2. Requisitos Não Funcionais

### Segurança (RNF-SEC)

- **RNF-SEC-01** [MVP] Senhas devem ser armazenadas com hash Argon2id (nunca em texto plano ou com hash reversível).
- **RNF-SEC-02** [MVP] Toda comunicação em produção deve ocorrer via HTTPS; cookies de sessão marcados `Secure`.
- **RNF-SEC-03** [MVP] Toda rota que acessa dado de workspace deve validar que o usuário autenticado é membro daquele workspace, no servidor, independentemente do que o cliente envie.
- **RNF-SEC-04** [MVP] O sistema deve aplicar rate limiting em endpoints de autenticação e, de forma mais permissiva, na API em geral.
- **RNF-SEC-05** [MVP] O sistema deve ser protegido contra CSRF nas rotas que dependem de cookie (refresh de sessão).
- **RNF-SEC-06** [MVP] Toda entrada de usuário deve ser validada no schema antes de alcançar a camada de negócio (sem exceção).

### Performance (RNF-PERF)

- **RNF-PERF-01** [MVP] Endpoints de listagem devem responder em p95 < 300ms com até 10 mil issues por workspace (assumindo índices corretos, ver `docs/03-database.md`).
- **RNF-PERF-02** Toda listagem deve ser paginada; nenhum endpoint deve retornar coleção completa sem limite.
- **RNF-PERF-03** O frontend deve aplicar atualização otimista em mutações de alta frequência (mudança de status, drag-and-drop no board).

### Disponibilidade e Confiabilidade (RNF-REL)

- **RNF-REL-01** Migrações de banco devem ser reversíveis e aplicadas sem downtime para mudanças aditivas (nova coluna nullable, nova tabela).
- **RNF-REL-02** [MVP] Erros não tratados nunca devem expor stack trace ou detalhe interno ao cliente — apenas ao log estruturado do servidor.

### Manutenibilidade (RNF-MAINT)

- **RNF-MAINT-01** [MVP] Toda regra de negócio nova deve ter teste unitário de service antes de ser considerada concluída (ver checklist em `CLAUDE.md` §18).
- **RNF-MAINT-02** [MVP] O código deve passar lint, format e type-check sem erros antes de qualquer merge.
- **RNF-MAINT-03** [MVP] Nenhuma camada pode pular a hierarquia definida em `CLAUDE.md` §3 (router → service → repository).

### Usabilidade (RNF-UX)

- **RNF-UX-01** [MVP] O frontend deve ser responsivo para desktop (prioridade) e utilizável em tablet; mobile nativo está fora de escopo.
- **RNF-UX-02** [MVP] Toda ação destrutiva (excluir issue, remover membro) deve exigir confirmação explícita.

### Observabilidade (RNF-OBS)

- **RNF-OBS-01** [MVP] Toda requisição deve gerar um `request_id` rastreável em log estruturado ponta a ponta.
- **RNF-OBS-02** Erros 5xx devem ser agregáveis por tipo/rota para permitir priorização (mesmo que, no MVP, isso seja apenas via log estruturado sem dashboard dedicado).

### Portabilidade (RNF-PORT)

- **RNF-PORT-01** [MVP] O ambiente de desenvolvimento deve ser reproduzível via Docker Compose (Postgres + Redis + API + Web), documentado (implementação de containers ocorre a partir da Sprint 1 — fora de escopo desta Sprint 0, ver `CLAUDE.md`).
