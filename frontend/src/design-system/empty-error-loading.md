# Empty / Error / Loading States

`shared/components/feedback/` reúne os estados de "não há dado normal para mostrar
aqui" — oito componentes, todos `py-16` + conteúdo centralizado, mas em três famílias
visuais distintas conforme o papel:

## 1. Bloco inline com moldura sólida — `EmptyState`

`border` sólida (não tracejada), ícone em `EmptyMedia` (sobre `ui/empty.tsx`),
título + descrição + ação opcional. Para "esta lista existe e está genuinamente vazia"
— o caso mais comum do app. 10 call sites: `IssuesEmptyState`/`ProjectsEmptyState` e
os cards do Dashboard (`Minhas issues`/`Atividade recente` quando não há dado).
Confirmado visualmente na Sprint 13.4 em tema claro e escuro.

## 2. Bloco inline com moldura tracejada + retry — `ErrorState`, `OfflineState`

`border border-dashed` + `Button variant="outline"` "Tentar novamente" quando
`onRetry` é passado. Para "a operação falhou, mas o usuário pode tentar de novo sem
sair da tela". `ErrorState` tem 12 call sites (toda listagem paginada:
`Issues`/`Projects`/`Labels`). `OfflineState` está pronto desde a Sprint 9
mas **sem call site** — depende de `navigator.onLine`/evento `offline`, que é
responsabilidade de quem consome, ainda não implementada em nenhuma feature.

A moldura tracejada vs. sólida é a distinção visual entre "vazio" (1) e "falhou" (2) —
não é uma escolha arbitrária, é consistente nos dois consumidores reais.

## 3. Bloco sem moldura — identidade/permissão/sucesso

`NotFoundState`, `ForbiddenState`, `LoadingState`, `SuccessState`, `UnauthorizedState`
não têm `border` — o conteúdo ocupa a tela/bloco inteiro, não é um "buraco" dentro de
uma lista. Dessa família, só `NotFoundState` tem call site hoje (`pages/
NotFoundPage.tsx`, que só compõe o componente). `ForbiddenState`/`LoadingState`/
`SuccessState`/`UnauthorizedState` são fundação da Sprint 9 sem call site ainda — mesmo
status que outros componentes preparados adiantados (ver `README.md`), não confundir
com código morto.

## Skeletons — carregando, não vazio/erro

`shared/components/skeletons/` (`ListSkeleton`, `CardSkeleton`, `TableSkeleton`,
`KanbanSkeleton`, `PageSkeleton`) são o estado "carregando" de uma lista/página — nunca
`LoadingState` (esse é para bloco/tela cheia fora do fluxo de listagem, ex.: uma ação
assíncrona que não é "buscar uma lista"). `ListSkeleton` é o único com consumidor real
hoje (`Issues`/`Projects`/`Labels`); os demais aguardam a tela que precisar deles (ver
`tables.md` sobre `TableSkeleton`).

## Fluxo padrão de uma listagem (referência cruzada)

```
FilterBar (busca + filtros + ação "criar")
  ↓
ListSkeleton (loading) | ErrorState (erro) | <Feature>Table + Pagination (dado) | EmptyState (vazio)
```

Ver `tables.md`. Confirmado nas três listagens (`Issues`/`Projects`/`Labels`) durante a
revisão visual da Sprint 13.4, tema claro e escuro.
