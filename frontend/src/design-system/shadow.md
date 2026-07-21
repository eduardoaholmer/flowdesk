# Shadow

Fonte de verdade: `src/shared/theme/tokens/shadow.ts` (`shadowScale`) —
`shadow-xs` → `shadow-xl`, classes Tailwind já em uso, não uma escala nova.

## Onde cada nível já aparece

| Classe      | Uso hoje                                                              |
| ----------- | --------------------------------------------------------------------- |
| `shadow-md` | `DropdownMenu`/`Popover` (elevação de menu flutuante)                 |
| `shadow-lg` | `Dialog`/`Sheet`/`DropdownMenuSubContent` (elevação de overlay modal) |

A paleta (Milestone 3, ADR-019) é uma rampa de neutros quentes de baixo croma, não
uma cor viva — a sombra continua sendo o principal sinal visual de "isto está
flutuando acima do conteúdo", não a cor de fundo. `StatCard`/`InfoCard`
(`shared/components/data-display/`) herdam a elevação de `Card` (`ring-1
ring-foreground/10` em repouso, `hover:shadow-sm` desde a Sprint 13.3/M3, ver
`cards.md`/`radius.md`/`elevation.md`) — nenhum deles declara sombra própria.

`IssueBoardCard`/`IssueBoardCardPreview` (Sprint 18.2, M7) são a única exceção: um
`box-shadow` inline one-off (`0 1px 2px rgba(20,19,15,.05)`), valor literal do
handoff de redesign, não a escala `shadowScale`/`--sh`. Mais sutil que qualquer
classe já pronta — reservado ao cartão de board por ser o único elemento
arrastável do app (o sinal de profundidade ajuda a diferenciar cartão de coluna).
