# Icons

Biblioteca: `lucide-react` (`iconLibrary: "lucide"` em `components.json`) — nenhuma
outra biblioteca de ícone deveria entrar no projeto sem justificativa (duplicaria o
conjunto já disponível).

## Tamanhos

Fonte de verdade: `src/shared/theme/tokens/sizes.ts` (`sizeTokens`) — classes
`size-*` do Tailwind já em uso, levantadas a partir do código real (não inventadas):
`size-2` até `size-10`. Uso predominante hoje:

| Contexto                                                            | Classe               |
| ------------------------------------------------------------------- | -------------------- |
| Ícone inline em botão/badge (padrão)                                | `size-4`             |
| Ícone em texto pequeno (ex.: `IssuePriorityBadge`)                  | `size-3.5`           |
| Ícone de estado vazio/erro (`EmptyState`/`ErrorState`/`feedback/*`) | `size-8`             |
| Avatar padrão / `size-lg`                                           | `size-8` / `size-10` |

## Regra de composição com texto

Ícone antes do texto, `gap-1.5`/`gap-2` (nunca margem manual em um lado só) — ver
`StatusBadge`, `ActionMenu`, qualquer botão com ícone + label no projeto hoje.
