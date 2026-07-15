# Spacing

Fonte de verdade: `src/shared/theme/tokens/spacing.ts` (`spacingScale`) — a escala
default do Tailwind (base 4px), **não redefinida**: `[0, 1, 2, 3, 4, 5, 6, 8, 10, 12,
16, 20, 24, 32]` (em unidades de `0.25rem`, ex. `4` = `1rem`/16px).

## Uso no dia a dia

Sempre via classe utilitária Tailwind (`p-4`, `gap-2`, `space-y-6`) — `spacingScale`
existe só para consumo em TS/JS (ex.: calcular um offset numérico fora de className),
não para substituir a classe no JSX do dia a dia.

## Onde o ritmo de espaçamento já está resolvido

- **Padding de página**: `PageContainer` (`shared/components/layout/`) —
  `px-4 py-6 sm:px-6 lg:px-8`. Nenhuma página deve declarar seu próprio padding de
  página solto.
- **Gap entre seções de uma página**: convenção existente é `flex flex-col gap-4`
  (ver `IssuesListPage`/`ProjectsListPage`/`LabelsListPage`).
- **Régua entre seções**: `SectionDivider` (`shared/components/typography/`) aplica
  `my-6` — não um valor solto por chamada.
- **Espaçamento interno de Card**: `--card-spacing` (`ui/card.tsx`), `--spacing(4)`
  por padrão, `--spacing(3)` no variant `size="sm"` — já centralizado no próprio
  primitivo, não redeclarado por quem usa `Card`.
