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

## 2. Componentes compartilhados (`src/shared/`)

- `shared/components/`: design system puro (Button, Input, Modal, Dropdown, Toast, Avatar, Badge) — construído sobre primitivos `shadcn/ui`/Radix, sem conhecimento de domínio (um `Badge` não sabe o que é uma `Issue`; recebe `color` e `label` como props).
- `shared/hooks/`: hooks genéricos sem domínio (`useDebounce`, `useMediaQuery`, `useLocalStorage`).
- `shared/lib/`: cliente HTTP central (`httpClient.ts` — wrapper de `fetch` com injeção de `Authorization`, tratamento de 401 disparando refresh, parse do envelope de erro padrão), formatação de data, utilitários puros.

Regra: se um componente de `shared/` precisar conhecer o conceito de "Issue" ou "Workspace", ele está no lugar errado — deve migrar para dentro da feature correspondente. Esse teste ("este componente sabe o nome de uma entidade de domínio?") é o critério objetivo usado em review para decidir `shared/` vs. `features/*`.

## 3. Layouts

- `AppLayout`: casca autenticada — sidebar (workspaces, times, navegação), topbar (busca, avatar, notificações), área de conteúdo roteada.
- `AuthLayout`: casca para telas de login/registro (sem sidebar), centrada, minimalista.
- `WorkspaceLayout`: aninhado dentro de `AppLayout`, injeta o `workspace_id` ativo no contexto de rota e carrega dados de nível workspace (papel do usuário, lista de times) uma vez para todas as páginas filhas.

## 4. Gerenciamento de estado e cache

Separação estrita (ADR-004, também descrita em `docs/02-architecture.md` §3):

- **TanStack Query = estado de servidor.** Toda entidade que existe no backend (issues, comments, workspaces, members) é lida e escrita exclusivamente através de queries/mutations. Query keys seguem convenção hierárquica: `['workspaces', workspaceId, 'issues', { filters }]` — invalidação de cache usa prefixo (`invalidateQueries(['workspaces', workspaceId, 'issues'])` invalida toda variação de filtro).
- **Zustand = estado de cliente.** UI efêmera que não existe no backend: sidebar colapsada, tema, filtros em edição antes de aplicar, estado de modais. Stores são pequenos e por feature (`useIssueFilterStore`), não um único store global monolítico.
- **Mutations otimistas** (RNF-PERF-03): mudança de status via drag-and-drop no board atualiza o cache do TanStack Query imediatamente (`onMutate`), faz rollback automático em `onError`, e reconcilia em `onSettled`. Esse padrão é obrigatório para as duas interações de maior frequência do produto (mudança de status, reordenação no board) — não é obrigatório para mutations de baixa frequência (criar time, convidar membro), onde esperar a resposta do servidor antes de atualizar a UI é aceitável e mais simples.
- **Sem estado de servidor duplicado**: é proibido copiar dado de uma query do TanStack Query para dentro de um store Zustand "para facilitar o acesso" — isso recria a classe de bug (cache dessincronizado) que a separação existe para evitar.

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

## 6. Autenticação (frontend)

- Access token mantido **em memória** (variável de módulo/contexto React), nunca em `localStorage`/`sessionStorage` — mitiga exfiltração via XSS (ver `docs/07-security.md`). Perda de estado em refresh de página é resolvida chamando `POST /auth/refresh` (cookie HttpOnly) no bootstrap da aplicação para obter um novo access token antes de renderizar rotas protegidas.
- `httpClient` intercepta resposta `401`, tenta `refresh` uma única vez de forma transparente, e só então propaga o erro (evita que toda tela precise tratar expiração de token manualmente).
- Estado de "usuário atual" é uma query do TanStack Query (`['auth', 'me']`), não um store separado — é dado de servidor.

## 7. Organização das páginas

Páginas (`src/app/pages/` ou diretamente como entrypoint de rota) são **composição fina**: montam layout + componentes de feature, não contêm lógica de negócio nem chamadas HTTP diretas. Uma página de detalhe de issue, por exemplo, é essencialmente `<IssueDetail issueNumber={...} />` — toda a lógica vive dentro da feature `issues`. Isso mantém páginas triviais de ler e torna componentes de feature testáveis isoladamente da rota que os hospeda.

## 8. Convenções de componentes

- Componentes funcionais + hooks exclusivamente; sem class components.
- Um componente por arquivo, nome do arquivo = nome do componente (`IssueCard.tsx` exporta `IssueCard`).
- Props tipadas via `interface Props { ... }` declarada acima do componente, nunca `React.FC<Props>` (evita problemas de inferência de `children` implícito e é a recomendação atual da comunidade React/TS).
- Composição sobre configuração: um componente com mais de ~5 props booleanas é sinal de que deveria ser dividido em componentes compostos (`<Modal><Modal.Header/><Modal.Body/></Modal>`) em vez de crescer flags.
- Lógica não-trivial de um componente (mais de ~2 `useEffect`/`useMemo` relacionados) é extraída para um hook customizado nomeado pelo propósito (`useIssueBoard`), não deixada inline — mantém o componente focado em renderização.
- Acessibilidade: todo componente interativo do design system (`shared/components/`) implementa atributos ARIA e navegação por teclado corretos uma única vez; features consomem esse componente e herdam o comportamento — acessibilidade não é responsabilidade repetida por feature.
