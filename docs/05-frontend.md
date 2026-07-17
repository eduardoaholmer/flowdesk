# 05 — Frontend

Stack: React 19 + TypeScript 5 + Vite (SPA), React Router v6, TanStack Query, Zustand, React Hook Form + Zod, Tailwind CSS + shadcn/ui. Justificativa de cada escolha em ADR-003/ADR-004 (`docs/09-decision-log.md`).

## 1. Estrutura das Features

Organização por domínio (feature-based), não por tipo técnico — ver `CLAUDE.md` §12/§13. Cada feature em `src/features/<nome>/` é dona de:

```
features/issues/
├── components/         # componentes específicos desta feature (IssueCard, IssueBoard, IssueDetail)
├── hooks/               # hooks que orquestram query/mutation + regra de UI (useIssueBoard, useUpdateIssueStatus)
├── api.ts               # funções de chamada HTTP + definição de query keys do TanStack Query
├── types.ts              # tipos TypeScript do domínio (derivados/alinhados ao schema Pydantic do backend)
└── index.ts              # exports públicos da feature (o que outras features podem importar)
```

Regra de fronteira: uma feature só importa de outra feature através do seu `index.ts` (barrel export) — nunca um import profundo tipo `features/issues/components/IssueCard` a partir de `features/projects`. Isso preserva a mesma lógica de encapsulamento de agregado do backend (§6 de `docs/02-architecture.md`), agora no frontend.

> **Nota (pós-implementação, Sprint 6/7)**: a árvore acima é o esboço original da Sprint 0. A implementação real de `features/projects/` e `features/issues/` usa `hooks.ts` (arquivo único, não pasta `hooks/`) e não tem `index.ts` — outro código importa diretamente de `features/<nome>/components/Arquivo` e `features/<nome>/hooks`. Sem barrel export, a "regra de fronteira" acima não é reforçada por import path hoje; a convenção seguida na prática é: um componente de uma feature nunca importa de dentro de `components/` de outra feature (só de `hooks.ts`/`api.ts`/`types.ts`, que são a interface pública de fato), o que preserva o mesmo encapsulamento sem a indireção de um barrel. Um componente puramente compartilhado sem lógica de domínio (ex.: `ConfirmActionDialog`) vive em `shared/components/`, não duplicado por feature — ver §2.

## 2. Componentes compartilhados (`src/shared/`)

- `shared/components/`: design system puro (Button, Input, Modal, Dropdown, Toast, Avatar, Badge) — construído sobre primitivos `shadcn/ui`/Radix, sem conhecimento de domínio (um `Badge` não sabe o que é uma `Issue`; recebe `color` e `label` como props).
- `shared/hooks/`: hooks genéricos sem domínio (`useDebounce`, `useMediaQuery`, `useLocalStorage`).
- `shared/lib/`: cliente HTTP central (`httpClient.ts` — wrapper de `fetch` com injeção de `Authorization`, tratamento de 401 disparando refresh, parse do envelope de erro padrão), formatação de data, utilitários puros.

Regra: se um componente de `shared/` precisar conhecer o conceito de "Issue" ou "Workspace", ele está no lugar errado — deve migrar para dentro da feature correspondente. Esse teste ("este componente sabe o nome de uma entidade de domínio?") é o critério objetivo usado em review para decidir `shared/` vs. `features/*`.

> **Nota (pós-implementação, Sprint 8.5)**: além do já existente, `shared/` ganhou `components/EmptyState.tsx` (generaliza o padrão de estado vazio antes duplicado em `IssuesEmptyState`/`ProjectsEmptyState` — cada feature continua dona da própria cópia/ícone/ação, só a casca visual é compartilhada), `components/ErrorBoundary.tsx` (error boundary de árvore, complementar — não substituto — ao tratamento de erro de query/mutation por feature, `docs/10-coding-standards.md` §9), `components/skeletons/` (`PageSkeleton`, `CardSkeleton`, `TableSkeleton`, `ListSkeleton`, `KanbanSkeleton`) e `theme/tokens.ts` (referência tipada aos design tokens, ver §9 abaixo).

## 3. Layouts

- `AppLayout`: casca autenticada — sidebar (workspaces, navegação), topbar (breadcrumb, busca, notificações, avatar), área de conteúdo roteada.
- `AuthLayout`: casca para a tela de login (sem sidebar), centrada, minimalista.
- `EmptyLayout`: casca mínima centrada sem sidebar/topbar, para estados sem workspace ainda resolvido (ex.: onboarding "crie seu primeiro workspace").

> **Nota (pós-implementação, Sprint 8.5)**: `AuthLayout` e `EmptyLayout` existem de fato desde a Sprint 8.5 (`src/shared/components/layout/`) — a nota da Sprint 7 abaixo, que dizia que só `AppLayout` existia, está superada nesse ponto específico. `WorkspaceLayout` continua não existindo (não há dado de nível "workspace" carregado uma vez para páginas filhas além do que `useWorkspace`/`useCurrentUser` já resolvem via TanStack Query) — não há necessidade real dele até que uma página filha precise de mais contexto de workspace do que isso.

## 4. Gerenciamento de estado e cache

Separação estrita (ADR-004, também descrita em `docs/02-architecture.md` §3):

- **TanStack Query = estado de servidor.** Toda entidade que existe no backend (issues, comments, workspaces, members) é lida e escrita exclusivamente através de queries/mutations. Query keys seguem convenção hierárquica: `['workspaces', workspaceId, 'issues', { filters }]` — invalidação de cache usa prefixo (`invalidateQueries(['workspaces', workspaceId, 'issues'])` invalida toda variação de filtro).
- **Zustand = estado de cliente.** UI efêmera que não existe no backend: sidebar colapsada, tema, filtros em edição antes de aplicar, estado de modais. Stores são pequenos e por feature (`useIssueFilterStore`), não um único store global monolítico.
- **Mutations otimistas** (RNF-PERF-03): mudança de status via drag-and-drop no board atualiza o cache do TanStack Query imediatamente (`onMutate`), faz rollback automático em `onError`, e reconcilia em `onSettled`. Esse padrão é obrigatório para as duas interações de maior frequência do produto (mudança de status, reordenação no board) — não é obrigatório para mutations de baixa frequência (criar time, convidar membro), onde esperar a resposta do servidor antes de atualizar a UI é aceitável e mais simples.
- **Sem estado de servidor duplicado**: é proibido copiar dado de uma query do TanStack Query para dentro de um store Zustand "para facilitar o acesso" — isso recria a classe de bug (cache dessincronizado) que a separação existe para evitar.

> **Nota (pós-implementação, Sprint 8.5)**: `shared/stores/uiStore.ts` é o primeiro store Zustand de UI cliente-only do projeto (colapso da Sidebar, estado do menu mobile) — `authStore.ts` já existia, mas guarda sessão, não UI. Novo estado efêmero de UI (não específico de uma feature) entra em `uiStore`, não em stores novos por componente, até que o volume justifique separar.

## 5. Rotas

React Router v6, roteamento declarado centralmente em `src/routes/`, não espalhado dentro de cada feature (facilita ver a árvore completa de navegação em um único lugar):

```
/login, /register                                    (AuthLayout)
/w/:workspaceSlug                                     (AppLayout > WorkspaceLayout) → redireciona para /issues
/w/:workspaceSlug/settings/members
/w/:workspaceSlug/settings/teams
/w/:workspaceSlug/teams/:teamKey/board                (board por status)
/w/:workspaceSlug/teams/:teamKey/issues/:issueNumber  (detalhe de issue)
/w/:workspaceSlug/issues?...                          (listagem/busca cross-team)
```

- Rotas autenticadas são protegidas por um `RequireAuth` wrapper que verifica sessão válida (via `useAuth` — deriva de uma query `auth/me` com `staleTime` alto) antes de renderizar; ausência de sessão redireciona para `/login` preservando a URL de destino (`?redirect=`).
- `workspaceSlug` na URL (não `workspace_id`) por ergonomia de compartilhamento de link; resolução para `workspace_id` acontece uma vez no `WorkspaceLayout` e é passada via contexto para as páginas filhas — páginas nunca re-resolvem o slug individualmente.

> **Nota (pós-implementação, Sprint 7)**: a árvore acima (esboço da Sprint 0) pressupõe `Team`/board por time, não implementados (ADR-012, `docs/09-decision-log.md`). As rotas reais, centralizadas em `src/app/router.tsx` dentro de `AppLayout`/`RequireAuth`, são: `/w/:workspaceSlug/issues` (listagem, com filtros/busca/ordenação/paginação via query string) e `/w/:workspaceSlug/issues/:issueId` (detalhe, endereçada por UUID, não por `teamKey` + `number` — não há `Team` para compor a URL). O mesmo padrão já valia para `/w/:workspaceSlug/projects[/:projectId]` desde a Sprint 6. Não existe `WorkspaceLayout` como componente próprio — `AppLayout` (sidebar + topbar) já cobre o caso de rota autenticada. `AuthLayout` passou a existir na Sprint 8.5 (ver nota em §3); `/login` o usa, mas continua fora de `AppLayout`/`RequireAuth`.

> **Nota (pós-implementação, Sprint 8)**: só Labels ganhou rota própria (`/w/:workspaceSlug/labels`, gestão de labels do workspace, `LabelsPage`/`LabelsListPage`) — Comentários e Anexos não têm página/rota dedicada, porque não são recursos navegáveis por si (não existe "ver um comentário" fora do contexto da issue-mãe). Em vez disso, `CommentList` e `AttachmentList` são componentes auto-contidos (buscam seus próprios dados via `useComments`/`useAttachments`, recebem só `workspaceId`/`issueId` como props) compostos diretamente dentro de `IssueDetailView` (`features/issues/components/`), junto de `IssueLabelPicker` (`features/labels/`) para aplicar/remover label na issue. Nenhum dos três é importado de `features/issues/` para dentro de `IssueDetailView` via um barrel — reforça a convenção já registrada na nota da Sprint 6/7 acima (import direto de `hooks.ts`/`components/Arquivo`, nunca de dentro de `components/` de uma feature para regra de negócio de outra).

> **Nota (pós-implementação, Sprint 10/M2)**: duas rotas novas, ambas dentro de `AppLayout`/`RequireAuth` como as demais. `/w/:workspaceSlug/settings` (`WorkspaceSettingsPage`, `features/workspaces/components/WorkspaceSettingsPage.tsx`) — abas Geral/Membros/Convites, controles de mutação (renomear, excluir, convidar, alterar papel, remover membro) gated client-side por `profile.workspaces[].role`, sempre reforçado pela autorização real do servidor. `/invitations/:token/accept` (`InvitationAcceptPage`) — só existe dentro da área autenticada (aceitar convite exige `get_current_user` no backend, ADR-009), usa `EmptyLayout` como `HomePage` em vez de sidebar/topbar, já que ainda não há um workspace ativo resolvido. `features/dashboard/` (placeholder da Sprint 8.5, nunca agendado) foi removido nesta sprint — ver ADR-018. A paleta de comandos (`shared/components/command-palette/CommandPalette.tsx`, montada uma vez em `AppLayout`) não é uma rota — é um overlay global acionável de qualquer página autenticada via `Cmd/Ctrl+K` ou o botão de busca do `Topbar`.

## 6. Autenticação (frontend)

- Access token mantido **em memória** (variável de módulo/contexto React), nunca em `localStorage`/`sessionStorage` — mitiga exfiltração via XSS (ver `docs/07-security.md`). Perda de estado em refresh de página é resolvida chamando `POST /auth/refresh` (cookie HttpOnly) no bootstrap da aplicação para obter um novo access token antes de renderizar rotas protegidas.
- `httpClient` intercepta resposta `401`, tenta `refresh` uma única vez de forma transparente, e só então propaga o erro (evita que toda tela precise tratar expiração de token manualmente).
- Estado de "usuário atual" é uma query do TanStack Query (`['auth', 'me']`), não um store separado — é dado de servidor.
- `RequireAuth` redireciona para `/login` gravando `state: { from: location }`; `LoginPage` lê isso via `shared/lib/routes.ts::resolveLoginRedirect` e devolve o usuário ao destino original após o login (ex.: um link de convite acessado desconectado) em vez de sempre cair em `/` (Sprint 12.1/M2 fase 2, ADR-021 — bug encontrado na auditoria de gap, `state.from` já existia desde a introdução de `RequireAuth` mas nunca era lido).

## 7. Organização das páginas

Páginas (`src/app/pages/` ou diretamente como entrypoint de rota) são **composição fina**: montam layout + componentes de feature, não contêm lógica de negócio nem chamadas HTTP diretas. Uma página de detalhe de issue, por exemplo, é essencialmente `<IssueDetail issueNumber={...} />` — toda a lógica vive dentro da feature `issues`. Isso mantém páginas triviais de ler e torna componentes de feature testáveis isoladamente da rota que os hospeda.

## 8. Convenções de componentes

- Componentes funcionais + hooks exclusivamente; sem class components — única exceção deliberada é `shared/components/ErrorBoundary.tsx` (Sprint 8.5), porque React só expõe `componentDidCatch`/`getDerivedStateFromError` via class component; nenhum outro componente do projeto deve seguir esse exemplo.
- Um componente por arquivo, nome do arquivo = nome do componente (`IssueCard.tsx` exporta `IssueCard`).
- Props tipadas via `interface Props { ... }` declarada acima do componente, nunca `React.FC<Props>` (evita problemas de inferência de `children` implícito e é a recomendação atual da comunidade React/TS).
- Composição sobre configuração: um componente com mais de ~5 props booleanas é sinal de que deveria ser dividido em componentes compostos (`<Modal><Modal.Header/><Modal.Body/></Modal>`) em vez de crescer flags.
- Lógica não-trivial de um componente (mais de ~2 `useEffect`/`useMemo` relacionados) é extraída para um hook customizado nomeado pelo propósito (`useIssueBoard`), não deixada inline — mantém o componente focado em renderização.
- Acessibilidade: todo componente interativo do design system (`shared/components/`) implementa atributos ARIA e navegação por teclado corretos uma única vez; features consomem esse componente e herdam o comportamento — acessibilidade não é responsabilidade repetida por feature.

## 9. Design tokens e fundação compartilhada (Sprint 8.5)

`shared/theme/tokens.ts` é uma referência TS tipada aos design tokens do projeto — não redefine nem inventa valor nenhum, só aponta para a fonte de verdade real:

- **Cores, radius**: `--color-*`/`--radius-*` em `src/index.css` (inalterados desde a Sprint 0).
- **Espaçamento, tipografia, sombras**: escala default do Tailwind, já em uso em todo o projeto — `tokens.ts` só documenta quais classes são o vocabulário aceito, não redefine a escala.
- **Motion**: única categoria genuinamente nova — `--duration-fast/base/slow` e `--ease-standard/emphasized`, adicionados em `src/index.css`. Sem equivalente anterior no projeto; consumido via arbitrary value do Tailwind (`duration-[var(--duration-base)]`) ou, fora de className, via `motionTokens` em `tokens.ts`.

Nenhuma cor nova foi introduzida — esta sprint prepara a organização dos tokens, não a identidade visual (isso é escopo de uma sprint futura).

`shared/hooks/` ganhou `useBreakpoint`, `useMediaQuery`, `useDisclosure`, `useLocalStorage`, `usePrevious` (debounce já era coberto por `useDebouncedValue`, não duplicado). `shared/lib/` ganhou `date.ts`, `string.ts`, `number.ts`, `validation.ts` — funções puras, sem I/O; `date.ts`/`string.ts` já substituíram duplicação real encontrada em `CommentItem`, `IssueActivityTimeline`, `IssueDetailView`, `IssuesTable`, `ProjectDetailView` (formatação de data e iniciais de nome, antes copiadas por componente).

## 10. Command palette e notificações (Sprint 10/M2)

- `shared/components/command-palette/`: `CommandPalette.tsx` (montado uma vez em `AppLayout`, não por página), `commands.ts` (registro de comandos estáticos — uma função `buildXCommands` por grupo: navegação, troca de workspace, utilitários de tema/logout — extensível sem tocar o componente) e `useRecentCommands.ts` (persistência em `localStorage`, só para comandos com destino de navegação). Vive em `shared/` e não em `features/` porque não pertence a um único domínio — compõe issues, projetos, workspaces e navegação estrutural em um único overlay (mesmo critério de `docs/05-frontend.md` §2: não tem conhecimento de domínio próprio, só orquestra o que outras features já expõem via `api.ts`/`hooks.ts`). Estado de aberto/fechado vive em `shared/stores/uiStore.ts` (`isCommandPaletteOpen`) — não em estado local do componente — porque tanto o atalho global (`Cmd/Ctrl+K`, ouvido dentro do próprio `CommandPalette`) quanto o botão de busca do `Topbar` precisam acionar a mesma instância. Busca de issues/projetos reaproveita `listIssues`/`listProjects` já existentes (não há endpoint de busca dedicado, ver ADR-018 Decisão 7).
- `features/notifications/`: primeira vez que o frontend consome os endpoints da Sprint 9 fase 1. `useRecentNotifications`/`useUnreadNotificationsCount` fazem polling (30s, `refetchInterval` do TanStack Query) — sem WebSocket ainda (`docs/08-roadmap.md`, Sprint 11+). `NotificationItem` (`features/notifications/components/`) é quem sabe formatar cada `NotificationType` em texto legível e resolver o link para a issue relacionada; `Topbar.tsx::TopbarNotifications` só compõe a lista, sem lógica de domínio própria — mesmo padrão de `CommentList`/`AttachmentList` dentro de `IssueDetailView` (nota da Sprint 8 em §5).
- `features/workspaces/components/`: `WorkspaceSettingsPage` (abas Geral/Membros/Convites), `WorkspaceGeneralSettings`, `WorkspaceMembersSettings`, `WorkspaceInvitationsSettings`, `InviteMemberDialog` — primeira UI real de administração de workspace (o backend existe desde as Sprints 4/5). Controles de mutação são gated client-side por papel (`profile.workspaces[].role`), sempre reforçado pela autorização real do servidor (`core/authorization.py`) — nunca a única linha de defesa.
