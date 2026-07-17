# 00 — Visão de Produto

> **Nota (pós-implementação, ADR-020)**: este documento descreve a visão *original* do produto, incluindo o corte de MVP decidido na Sprint 0. Duas premissas abaixo deixaram de ser verdade na execução real e nunca haviam sido corrigidas aqui até agora (gap de processo identificado na auditoria de 2026-07-16): (1) `Team`/workflow-por-time foi removido do domínio na Sprint 7 (ADR-012) — issues pertencem diretamente a um workspace, com status como enum fixo, não a um time com workflow configurável; (2) o board Kanban por status (§5) deixou de ser MVP — é hoje o Milestone 5 do roadmap executivo (`docs/08-roadmap.md`), um milestone dedicado e pós-engenharia-de-qualidade (M4), não mais um corte inicial. O texto abaixo não foi reescrito (é o registro histórico da decisão original de escopo) — `docs/08-roadmap.md` e `docs/09-decision-log.md` (ADR-007, ADR-012, ADR-018, ADR-020) são a fonte de verdade para o que de fato foi/será construído.

## 1. Objetivo do produto

FlowDesk é uma ferramenta de gestão de trabalho para times de produto e engenharia — organização de issues, projetos e ciclos de desenvolvimento — construída como alternativa de identidade própria ao Linear.

O objetivo de produto declarado (o que o usuário final ganha): permitir que um time pequeno registre, priorize e acompanhe o progresso do seu trabalho com o mínimo de fricção possível — criar uma issue deve levar segundos, mudar seu status deve ser um clique, e o time deve enxergar o estado real do trabalho sem precisar de reuniões de status.

O objetivo real deste repositório (por que ele existe): é um projeto de portfólio. Cada decisão de arquitetura documentada aqui existe também para ser **defensável em uma entrevista técnica** — não apenas "funciona", mas "eu sei por que fiz assim e o que eu trocaria se as condições fossem outras". Isso molda escolhas ao longo de todo o roadmap: preferimos implementar menos features com profundidade arquitetural correta (multi-tenancy real, RBAC real, testes reais) a implementar muitas features de forma rasa.

## 2. Público-alvo

- **Público-alvo do produto (fictício, para orientar decisões de UX/feature):** times pequenos e médios de produto/engenharia (5–50 pessoas) que precisam de um rastreador de issues rápido, sem a complexidade de ferramentas enterprise (Jira) nem a informalidade de um Kanban genérico (Trello).
- **Público-alvo real deste repositório:** recrutadores técnicos, tech leads e engenheiros seniores avaliando a capacidade do autor de projetar e construir um sistema multi-tenant com autenticação, RBAC, camadas bem definidas e um contrato de API consistente.

Essa dualidade é intencional e está registrada aqui porque ela explica por que, por exemplo, priorizamos "isolamento de workspace correto" antes de "integrações com Slack/GitHub" — a segunda é mais valiosa para um usuário real hipotético, a primeira é o que efetivamente demonstra competência de arquitetura.

## 3. Principais funcionalidades

Núcleo funcional do produto (detalhado por sprint em `docs/08-roadmap.md`):

- **Autenticação e contas**: cadastro, login, sessão via JWT + refresh token, logout, recuperação de senha (fora do MVP, ver §5).
- **Workspaces**: um usuário pode pertencer a múltiplos workspaces (tenants); convite de membros por e-mail; papéis (Owner/Admin/Member/Guest).
- **Times (Teams)**: subdivisão dentro de um workspace, cada um com seu próprio conjunto de issues e workflow de status.
- **Projetos**: agrupamento de issues com objetivo e prazo, atravessando ou não múltiplos times.
- **Issues**: unidade central de trabalho — título, descrição (rich text/markdown), status, prioridade, responsável, labels, estimativa, ciclo.
- **Ciclos (Cycles/Sprints)**: janelas de tempo fixas às quais issues são alocadas, com relatório de progresso.
- **Comentários**: discussão por issue, com menções.
- **Busca e filtros**: por status, responsável, label, prioridade, texto livre.
- **Notificações**: in-app (e, potencialmente, e-mail) para eventos relevantes (menção, atribuição, mudança de status em issue observada).
- **Atividade/Auditoria**: histórico de mudanças por issue (quem mudou o quê e quando).

## 4. Diferenciais

Diferenciais de produto (dentro da ficção do produto):

- Foco em velocidade percebida: qualquer ação (criar issue, mudar status) deve refletir na UI de forma otimista, sem esperar round-trip do servidor.
- Modelo de workflow por time (não um único board global) — cada time pode ter seus próprios estados sem forçar todo o workspace a um único fluxo.
- Command palette (busca/ação rápida via teclado) como cidadã de primeira classe, não um acréscimo.

Diferenciais de engenharia (o que realmente é avaliado num portfólio):

- Multi-tenancy com isolamento reforçado em duas camadas (autorização + filtro obrigatório no repository), não apenas "checagem de permissão na rota".
- Contrato de API deliberadamente versionado e documentado antes da implementação (`docs/04-api-design.md`), não descoberto organicamente durante o desenvolvimento.
- Estratégia de testes em pirâmide real (unit/integration/contract/E2E), aplicada desde a Sprint 1, não retroativamente.
- Decisões de arquitetura registradas como ADRs (`docs/09-decision-log.md`) — a capacidade de justificar trade-offs é parte do artefato de portfólio tanto quanto o código.

## 5. MVP

O MVP é o menor conjunto de funcionalidades que permite demonstrar o ciclo completo "criar conta → criar workspace → colaborar em issues" com todas as camadas de arquitetura (auth, RBAC, multi-tenancy, camadas backend, testes) já presentes e corretas — não um MVP raso que adia arquitetura para depois.

**Incluído no MVP:**
- Cadastro/login/logout com JWT + refresh token.
- Criação e gestão de workspace, convite de membros, papéis (Owner/Admin/Member).
- Criação de times dentro de um workspace.
- CRUD completo de issues (título, descrição, status, prioridade, responsável, labels).
- Comentários em issues.
- Listagem com filtros (status, responsável, label) e busca textual simples.
- Board (kanban) por status dentro de um time.

**Explicitamente fora do MVP** (adiado para o roadmap pós-MVP, `docs/08-roadmap.md`):
- Projetos e Ciclos (camada de planejamento acima da issue).
- Notificações (in-app e e-mail).
- Papel `Guest` com permissões restritas.
- Recuperação de senha por e-mail (login/senha básico é suficiente para demonstrar o padrão de auth).
- Integrações externas (GitHub, Slack).
- Command palette e atalhos de teclado avançados.
- Anexos de arquivo em issues/comentários.

Justificativa do corte: o MVP precisa provar a arquitetura multi-tenant + RBAC + camadas de principio a fim. Projetos/Ciclos são "mais do mesmo padrão" aplicado a outra entidade — de maior valor para completude de produto do que para novidade arquitetural — por isso vêm depois.

## 6. Roadmap de evolução (visão de alto nível)

Detalhamento completo em `docs/08-roadmap.md`. Visão de alto nível:

1. **Fundação** — setup de monorepo, CI, convenções, esqueleto das duas aplicações.
2. **Modelagem de domínio** — schema completo (models, repositories, migrations) para todo o domínio, antes de qualquer regra de negócio.
3. **Auth & Workspaces** — autenticação completa, multi-tenancy, RBAC básico.
4. **Núcleo de Issues** — CRUD de times e issues, board por status.
5. **Colaboração** — comentários, atividade/auditoria, busca e filtros avançados.
6. **Planejamento** — projetos e ciclos, relatórios de progresso.
7. **Polimento e observabilidade** — notificações, rate limiting, hardening de segurança, métricas.
8. **Extensões futuras (pós-portfólio)** — integrações externas, mobile, tempo real via WebSocket para colaboração ao vivo.
