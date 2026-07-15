# Cards

Primitivo: `ui/card.tsx` — `Card`, `CardHeader`, `CardTitle`, `CardDescription`,
`CardAction`, `CardContent`, `CardFooter` **já existem e cobrem o pedido de
"CardHeader"/"CardFooter"** — não foram recriados nesta sprint.

## Composições sobre `Card`

- **`StatCard`** (`shared/components/data-display/`) — uma métrica (label + valor +
  ícone + tendência opcional). Estado de carregamento via `CardSkeleton`
  (`shared/components/skeletons/`, `isLoading` prop). Pensado para o dashboard da
  Sprint 9 (`features/dashboard/`, hoje placeholder).
- **`InfoCard`** (`shared/components/data-display/`) — título + descrição + conteúdo
  livre, para blocos informativos genéricos (não uma métrica).
- **`MotionCard`** (`shared/components/motion/`) — resposta a hover/tap para um card
  clicável (ver `motion.md`). Compõe com `StatCard`/`InfoCard` envolvendo-os, não os
  substitui.

## Quando não usar `Card`

Uma linha de tabela (`ui/table.tsx`) ou um item de lista simples não precisa de
`Card` — usar `Card` para tudo que exibe uma coleção infla o DOM sem ganho visual.
Ver `tables.md`.
