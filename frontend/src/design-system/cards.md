# Cards

Primitivo: `ui/card.tsx` — `Card`, `CardHeader`, `CardTitle`, `CardDescription`,
`CardAction`, `CardContent`, `CardFooter` **já existem e cobrem o pedido de
"CardHeader"/"CardFooter"** — não foram recriados nesta sprint.

## Composições sobre `Card`

- **`StatCard`** (`shared/components/data-display/`) — uma métrica (label + valor +
  ícone + tendência opcional). Estado de carregamento via `CardSkeleton`
  (`shared/components/skeletons/`, `isLoading` prop). Seu consumidor original previsto
  era um dashboard — removido no Milestone 2 por não ter requisito de produto por
  trás (`docs/09-decision-log.md` ADR-018). Continua como fundação disponível sem
  call site real hoje; não force um consumidor só para "usá-lo".
- **`InfoCard`** (`shared/components/data-display/`) — título + descrição + conteúdo
  livre, para blocos informativos genéricos (não uma métrica). Também sem call site
  real hoje.

## Hover/resposta a interação

Um card clicável usa `transition-colors`/`transition-shadow` do Tailwind (ver
`motion.md` — o projeto não usa uma biblioteca de animação JS para isto).

## Quando não usar `Card`

Uma linha de tabela (`ui/table.tsx`) ou um item de lista simples não precisa de
`Card` — usar `Card` para tudo que exibe uma coleção infla o DOM sem ganho visual.
Ver `tables.md`.
