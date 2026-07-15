# Shadow

Fonte de verdade: `src/shared/theme/tokens/shadow.ts` (`shadowScale`) —
`shadow-xs` → `shadow-xl`, classes Tailwind já em uso, não uma escala nova.

## Onde cada nível já aparece

| Classe      | Uso hoje                                                              |
| ----------- | --------------------------------------------------------------------- |
| `shadow-md` | `DropdownMenu`/`Popover` (elevação de menu flutuante)                 |
| `shadow-lg` | `Dialog`/`Sheet`/`DropdownMenuSubContent` (elevação de overlay modal) |

A paleta é hoje grayscale (`--card`/`--popover` sem alpha) — a sombra é o principal
sinal visual de "isto está flutuando acima do conteúdo", não a cor. `StatCard`/
`InfoCard`/`MotionCard` (`shared/components/data-display/`, `.../motion/`) herdam a
sombra de `Card` (`ring-1 ring-foreground/10`, não `shadow-*`, ver `radius.md`/
`elevation.md`) — nenhum deles declara sombra própria.
