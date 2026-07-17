# Changelog

Todas as mudanças notáveis deste projeto são documentadas neste arquivo. O formato é baseado em
[Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/). Este projeto ainda não tem releases
versionados — o desenvolvimento acontece diretamente em `main`, sprint a sprint (ver
[`docs/08-roadmap.md`](./docs/08-roadmap.md)).

## [Unreleased]

### Sprint 12.3 (M2 fase 2) — Polimento da administração de workspace e navegação

- Listas de membros/convites (`WorkspaceMembersSettings`/`WorkspaceInvitationsSettings`)
  deixam de buscar `per_page` fixo (100) descartando `meta` — agora usam paginação real
  (`Pagination`, o mesmo componente das listas de issues/projetos) e a lista de membros ganha
  um filtro por papel (`OWNER`/`ADMIN`/`MEMBER`/`GUEST`), já suportado pelo backend.
  `useWorkspaceMembers` (usado por 4 outros lugares para resolver "todos os membros" como
  lookup) foi mantido intocado; `useWorkspaceMembersPage` é um hook novo e separado para a
  tela paginada.
- Breadcrumb de página de detalhe (`Topbar.tsx`) mostra o identificador real da issue/projeto
  (`FD-42`, nome do projeto) em vez do texto literal "Detalhe".
- `docs/04-api-design.md` corrigido: `PATCH /workspaces/{workspace_id}` documentava `OWNER`
  como único papel autorizado, mas a matriz real sempre concedeu `ADMIN` todas as permissões
  exceto excluir o workspace — código e frontend já concordavam, só a doc divergia.
- Corrige mais uma lacuna de infraestrutura de teste encontrada ao escrever os testes desta
  sprint: jsdom não implementa as APIs de ponteiro que o Radix `Select` usa ao abrir/fechar
  via clique — `tests/setup.ts` ganhou os polyfills necessários.

### Sprint 12.2 (M2 fase 2) — Recuperação de senha no frontend

- O backend de recuperação de senha (RF-AUTH-06, Sprint 9 fase 1/ADR-017) não tinha nenhuma
  UI — capacidade de servidor inteiramente inacessível.
- `ForgotPasswordPage`/`ForgotPasswordForm` (`/forgot-password`) — formulário de e-mail; após
  um `202` sempre mostra a tela de sucesso, nunca revelando se o e-mail existe ou não
  (anti-enumeration).
- `ResetPasswordPage`/`ResetPasswordForm` (`/reset-password/:token`) — formulário de nova
  senha; token inválido/expirado (`401`) mostra um atalho para solicitar um novo link em vez
  de deixar o usuário reenviar o mesmo formulário.
- Link "Esqueci minha senha" novo em `LoginForm`.
- `requestPasswordReset`/`confirmPasswordReset` novos em `features/auth/api.ts`.
- Corrige uma lacuna de infraestrutura de teste encontrada ao escrever os testes desta sprint:
  `tests/setup.ts` não tinha cleanup nem reset de mocks entre testes do mesmo arquivo (o
  auto-cleanup do Testing Library nunca era ativado, já que depende de `afterEach` em
  `globalThis` e `test.globals` não está ligado). Sem isso, um teste que não navega para longe
  do próprio formulário deixava elementos presos no DOM para o próximo teste do arquivo.

### Sprint 12.6 (M2 fase 2) — Dashboard: atividade recente e projetos ativos

- Completa a Home com os dois widgets identificados na auditoria da ADR-022 mas não
  implementados na 12.5.
- `RecentActivityWidget` — últimas notificações do usuário (`useRecentNotifications`),
  filtradas client-side pelo `workspace_id` do workspace ativo (o endpoint `GET /notifications`
  não aceita esse filtro no servidor); reaproveita `NotificationItem`/`useMarkNotificationRead`,
  os mesmos já usados por `TopbarNotifications`, sem duplicar lógica de descrição por tipo de
  notificação.
- `ActiveProjectsWidget` — projetos ativos (`useProjects(workspaceId, {status:"ACTIVE"})`),
  nome + data-alvo, empty state reaproveitando `CreateProjectDialog`.
- Ambos adicionados ao mesmo grid de `DashboardView` da 12.5, sem mudança estrutural.
- `DashboardPage` cresce de 4.10 kB para 6.15 kB de chunk próprio (code-splitting por rota
  inalterado, Sprint 8.6/ADR-015).

### Sprint 12.5 (M2 fase 2) — Dashboard/Home real: fundação, "Minhas issues" e atalhos

- `HomePage` (`/`) deixava de ter qualquer conteúdo próprio — só redirecionava direto para
  `/w/:slug/projects` (ou mostrava "crie seu primeiro workspace"). Testando o produto como um
  usuário único, isso fazia o app parecer vazio demais logo após o login. Reverte
  deliberadamente a remoção de `features/dashboard/` da Sprint 10 (ADR-018) sob um requisito
  novo — ver ADR-022 em `docs/09-decision-log.md`.
- Nova rota `/w/:workspaceSlug` (`routePatterns.workspaceHome`/`workspaceRoutes.home`);
  `HomePage` agora redireciona para ela em vez de `/projects` direto.
- `features/dashboard/` recriada só com `components/` (`DashboardView`, `MyIssuesWidget`,
  `QuickActions`) — composição pura sobre hooks já existentes de issues/projects, sem
  `api.ts`/`hooks.ts` próprio e sem nenhum endpoint novo.
- Widget "Minhas issues" (5 mais recentes atribuídas ao usuário) e atalhos rápidos
  (`CreateIssueDialog`/`CreateProjectDialog` reaproveitados, nenhum formulário novo).
- Entrada "Início" nova no `Sidebar` e no command palette.
- Primeiro uso real de `Card`/`CardHeader`/`CardAction`/`CardContent` (shadcn, instalado desde
  a Sprint 8.5, zero consumidor até agora).
- Sprint 12.6 (atividade recente + projetos ativos) fica planejada para uma próxima etapa,
  não implementada nesta sessão.

### Sprint 12.1 (M2 fase 2) — Corrige redirecionamento pós-login

- `RequireAuth` já gravava `state: { from: location }` ao redirecionar um usuário
  desconectado para `/login`, mas nada lia esse estado — todo login caía sempre em
  `/`, perdendo silenciosamente o destino original (ex.: um link de convite acessado
  sem sessão ativa). `shared/lib/routes.ts::resolveLoginRedirect` (novo, testado
  isoladamente) reconstrói o path+querystring original; `LoginPage`/`LoginForm`
  passam a navegar para esse destino após login bem-sucedido.
- Achado via uma auditoria de gap de M2 (ver ADR-021 em `docs/09-decision-log.md`) —
  primeira de quatro sub-sprints (12.1–12.4) que fecham a fase 2 do milestone.

### Sprint 11 (M3) — Ring Gate Brand System completion

- Paleta de cor: `src/index.css` deixa de ser o placeholder acromático do scaffold
  shadcn — `background`/`foreground`/`primary`/`card`/`popover`/`border`/`ring`/
  `sidebar-*` (dois temas) agora são uma rampa de neutros quentes derivada dos dois
  pontos travados da marca Ring Gate (`--brand-ink` `#14130F` / `--brand-paper`
  `#FAF8F3`, os mesmos já usados por `Logo`/favicon). Nenhuma cor nova — só a
  identidade já aprovada, estendida a toda superfície semântica. `--destructive`
  permanece vermelho puro (funcional, não marca), escurecido em modo claro para
  corrigir um contraste que ficava abaixo do mínimo AA (4.49:1 → 5.3:1).
- `Logo.tsx` passa a consumir `text-brand-ink dark:text-brand-paper` (tokens reais)
  em vez de hex inline.
- `PageContainer` passa a envolver `<Outlet/>` em `AppLayout` — toda rota autenticada
  ganha largura máxima/padding responsivo consistente de uma vez (antes: `p-6` sem
  limite de largura, zero página adotando o componente que deveria resolver isso).
- Removidos `framer-motion` (dependência) e os 10 componentes de
  `shared/components/motion/` (`FadeIn`/`FadeUp`/`MotionCard`/etc.) — zero call site
  real em qualquer tela do produto. Motion system do projeto agora é inteiramente
  CSS: os tokens `--duration-fast`/`--duration-base` passam a ser de fato consumidos
  pelos 8 primitivos Radix (`Dialog`/`Sheet`/`DropdownMenu`/`Popover`/`ContextMenu`/
  `HoverCard`/`Select`/`AlertDialog`) que antes hardcodavam `duration-100`/`200`.
- `prefers-reduced-motion` (novo): uma única regra CSS global zera duração de
  animação/transição em todo o projeto.
- `opacity.ts`/`containers.ts` (novos tokens) documentam convenções já em uso —
  nenhum valor novo.
- Ver ADR-019 em `docs/09-decision-log.md` para o racional completo, incluindo o que
  foi deliberadamente mantido (não removido) apesar de zero consumidor real hoje
  (`sidebar-*`/`chart-*`, `ContentContainer`).
- **Ressalva**: QA visual em navegador real não foi possível neste ambiente (faltam
  bibliotecas de sistema do Chromium headless, sem `sudo`) — contraste verificado
  computacionalmente (WCAG 2.1), não visualmente.

### Sprint 10 (M2) — Frontend Product Completeness

- Administração de workspace (`features/workspaces/`): nova `WorkspaceSettingsPage`
  (`/w/:workspaceSlug/settings`, abas Geral/Membros/Convites) — renomear/mudar
  slug/descrição e excluir workspace, convidar membro por e-mail com link de aceite
  copiável (`/invitations/:token/accept`, nova rota), cancelar convite pendente,
  alterar papel e remover membro, sair do workspace. Todos os endpoints já existiam
  desde as Sprints 4/5; esta sprint é a primeira UI real sobre eles. Controles de
  mutação gated client-side por papel, sempre reforçado pela autorização real do
  servidor.
- Command palette funcional (`shared/components/command-palette/`): atalho global
  `Cmd/Ctrl+K`, navegação por seção do workspace, troca de workspace, tema, logout,
  busca assíncrona debounced de issues/projetos (reaproveita endpoints de listagem
  existentes — não há endpoint de busca dedicado), comandos recentes persistidos em
  `localStorage`. Substitui a casca estática da Sprint 8.5 (`Topbar::TopbarSearch`
  não integrada).
- Notificações no frontend (`features/notifications/`): `Topbar::TopbarNotifications`
  deixa de ser um estado vazio fixo — consome `GET /notifications`,
  `PATCH /notifications/{id}`, `POST /notifications/mark-all-read` (todos da Sprint 9
  fase 1), com polling de 30s, badge de não lidas e link direto para a issue
  relacionada.
- `features/dashboard/` (placeholder vazio desde a Sprint 8.5, nunca agendado no
  roadmap) removido. Ver ADR-018 em `docs/09-decision-log.md`.
- Transferência de propriedade de workspace explicitamente fora de escopo — nenhum
  endpoint de backend existe para isso ainda (candidata a Milestone 6).

### Sprint 9 (fase 1) — Notificações, Recuperação de Senha, Rate Limiting

- Corrigidos 31 testes que estavam quebrados na árvore de trabalho: `IssueService`/
  `CommentService` haviam ganhado um argumento novo (`notification_service`) sem os
  fixtures de teste correspondentes serem atualizados. `features/notifications/`
  ganhou cobertura de teste unitário e de contrato completa (antes zero).
- RF-NOTIF-01/02: notificação in-app de menção (`CommentService._notify_mentions`) e
  de mudança de status de issue (`IssueService._notify_status_change`) — nenhuma das
  duas notifica quando o próprio autor da ação é o destinatário.
- RF-AUTH-06 (recuperação de senha): `POST /auth/password-reset/request` +
  `POST /auth/password-reset/confirm`. Token opaco de 256 bits, hash SHA-256 em
  repouso, uso único, expira em 30 min (`PASSWORD_RESET_TOKEN_EXPIRE_MINUTES`).
  Sempre `202` no `request` independente de o e-mail existir (anti-enumeration) — o
  token nunca é devolvido pela resposta HTTP, diferente do convite de workspace;
  `core/mail.py::MailSenderProtocol` (novo) é o ponto de extensão para um provedor de
  e-mail real. Confirmar o reset revoga todas as sessões ativas do usuário. Ver
  ADR-017 em `docs/09-decision-log.md`.
- Hardening de rate limit por rota: `password-reset/request`/`confirm` no mesmo tier
  de `login`/`register` (5/min por IP); novo tier de 60/min por IP para qualquer
  requisição sem Bearer válido a uma rota protegida (antes não era limitada de jeito
  nenhum).
- Pendente para uma fase 2 desta sprint: métricas básicas (5xx por rota, p95 por
  endpoint) e a revisão de segurança completa do checklist de `docs/07-security.md`.

### Identidade visual — FlowDesk "Ring Gate"

- Marca oficial integrada a partir da spec de produção do design (`brand/Logo.tsx`):
  símbolo em anel com duas barras, geometria travada em grid de 100u, cores de tinta
  `#14130F`/`#FAF8F3` (claro/escuro) sem uso de `filter: invert()`.
- Favicon (`public/favicon.svg`) substituído do placeholder gerado pela marca real,
  com variante clara/escura via `prefers-color-scheme`.
- `Logo` (lockups símbolo/horizontal/vertical) substitui o texto "FlowDesk" solto em
  `Topbar`/`LoginPage`.

### Sprint 8.7 — Production Readiness & Observability

- Envelope de erro padrão estendido a `RequestValidationError` e `HTTPException` do
  Starlette (antes vazavam o formato default do FastAPI em vez de `{"error": {...}}`).
- `GET /health/ready` (novo): checagens reais de banco, Redis e storage, com registro
  extensível para novas dependências (`core/health.py`); `GET /health` permanece liveness
  pura; `GET /version` ganhou `uptime_seconds`. Detalhe de falha (`str(exc)`) só aparece
  na resposta HTTP fora de produção — em produção fica só no log estruturado.
- Logging estruturado agora carrega `user_id` e `environment` em toda linha (além do
  `request_id` já existente); nova linha de access-log (`http_request`) por requisição.
- `SecurityHeadersMiddleware` novo (`X-Content-Type-Options`, `X-Frame-Options`,
  `Referrer-Policy`, `Permissions-Policy`, HSTS em produção); CORS com
  `allow_methods`/`allow_headers` explícitos em vez de `*`.
- `Settings` recusa subir com `ENVIRONMENT=production` usando a chave JWT de
  desenvolvimento; `environment` validado contra um conjunto fechado de valores.
- Docker multi-stage (`development`/`production`) para backend e frontend, agora
  copiando `poetry.lock` no build (antes só `pyproject.toml`, então a imagem podia
  re-resolver dependências fora do que o `pip-audit` do CI auditou);
  `docker-compose.prod.yml` novo demonstrando a topologia de produção. Ambos os
  targets `production` validados com `docker build` nesta sessão.
- CI: `pip-audit`/`npm audit` (não bloqueantes) e um novo job que builda as imagens
  Docker de produção (bloqueante); `.github/dependabot.yml` novo.
- `PRODUCTION_CHECKLIST.md` novo na raiz do repositório.
- Corrigido um bug de tipagem pré-existente em `core/rate_limit.py`: `Redis` (sem
  parâmetro genérico) e um `from_url()` sem retorno anotado — ambos exigem tratamento
  explícito (`Redis` sem `[str]`, `# type: ignore[no-untyped-call]` comentado) contra a
  versão de `redis`/`mypy` de fato pinada em `poetry.lock` (5.3.1 / 1.20.2). `mypy src`
  verde.
- Corrigido `tests/conftest.py::client`: `httpx.ASGITransport` não disparava o lifespan
  do FastAPI, então `app.state.started_at` nunca era setado e `GET /version` quebrava em
  qualquer teste de contrato.

### Sprint 8.6 — Architecture Hardening & Code Quality

- `shared/lib/routes.ts` (route builder único) substitui 11 pontos de template literal
  solto de rota espalhados pelo frontend.
- Code-splitting por rota em `router.tsx` (`React.lazy` + `Suspense`), endereçando o
  chunk único de 760kB da Sprint 8.5.
- `MAX_PICKER_PAGE_SIZE` (`shared/lib/constants.ts`) elimina `per_page: 100` repetido em
  4 arquivos.
- `frontend/.husky/pre-commit` mais defensivo: checa se o `pre-commit` do backend de
  fato executa antes de tentar ativar o venv.
- Barrel exports e múltiplos path aliases (pedidos originalmente) **não** foram
  adicionados — contradiziam decisão já documentada (`docs/05-frontend.md` §1,
  `docs/10-coding-standards.md` §3); ver ADR-015.

### Sprint 8.5 — Frontend Foundation & Design System Preparation

- Design system documentado (`src/design-system/*.md`) e primeiros componentes
  compostos reutilizáveis sob `shared/components/{layout, navigation, typography,
  data-display, forms, overlay, feedback, motion}/`, construídos sobre as primitivas
  shadcn/ui — fundação para a sprint de identidade visual/telas finais não precisar de
  refatoração estrutural.
- `Sidebar`/`Topbar` reescritos: colapsar, menu mobile (`Sheet`), seletor de workspace
  com dado real, breadcrumb estrutural, busca/notificações como pontos de extensão sem
  integração ainda.
- `shared/theme/tokens/*.ts` (um arquivo por categoria) substitui o antigo
  `theme/tokens.ts` único; `shared/stores/uiStore.ts` (primeiro store de UI
  cliente-only); `ErrorBoundary`, `EmptyState`/`ErrorState` (movidos para
  `feedback/`), skeletons genéricos (`PageSkeleton`/`CardSkeleton`/`TableSkeleton`/
  `ListSkeleton`/`KanbanSkeleton`) substituindo duplicação real entre issues/projects.
- Hooks (`useBreakpoint`, `useMediaQuery`, `useDisclosure`, `useLocalStorage`,
  `usePrevious`) e utils (`date.ts`, `string.ts`, `number.ts`, `validation.ts`) novos,
  substituindo duplicação real de formatação em 5 componentes de feature.
- 21 componentes shadcn/ui novos instalados via CLI.

### Sprint 1.5 — Bootstrap do repositório e hardening da fundação

- Repositório publicado no GitHub com metadados de projeto open source (LICENSE, CONTRIBUTING,
  CODE_OF_CONDUCT, SECURITY, templates de issue/PR, CODEOWNERS).
- Estrutura do frontend corrigida para bater com `CLAUDE.md` §13: componentes shadcn/ui e
  `utils.ts` movidos para `src/shared/`.
- Stack do frontend atualizada de React 18 (documentado por engano) para React 19 (o que
  realmente estava instalado) — ver `docs/09-decision-log.md` (ADR-003).
- Tooling de teste do frontend (Vitest + Testing Library) instalado e integrado ao CI, fechando
  o gap entre o que `CLAUDE.md` exige e o que existia.
- Hardening: containers de desenvolvimento (backend/frontend) rodando como usuário não-root;
  healthchecks adicionados para os serviços `backend`/`frontend` no Docker Compose;
  `X-Request-ID` validado antes de entrar nos logs estruturados.

### Sprint 0-1 — Fundação

- Monorepo (`backend/`, `frontend/`, `docs/`) com backend FastAPI e frontend React/Vite de pé,
  sem regra de negócio.
- Camadas transversais do backend (`core/`): configuração, sessão de banco (SQLAlchemy async),
  hierarquia de exceções de domínio, logging estruturado (structlog), middleware de
  request-id/CORS.
- Alembic configurado para migrações assíncronas.
- Shell do frontend: roteamento (React Router), providers (TanStack Query, tema claro/escuro),
  layout base (Sidebar/Topbar), componentes shadcn/ui.
- Docker Compose (Postgres 16, Redis 7, backend, frontend) e CI (GitHub Actions) rodando
  lint/format/type-check/testes em cada PR.
- Documentação completa do produto e da arquitetura em `docs/`.
