/**
 * Nomes dos tokens de cor semânticos definidos em `src/index.css` (`:root`/`.dark`).
 * Não redefine valores. Desde o Milestone 3 (`docs/09-decision-log.md` ADR-019), os
 * valores são a rampa de neutros quentes derivada dos dois pontos travados da marca
 * Ring Gate (`--brand-ink`/`--brand-paper`) — não mais o placeholder acromático do
 * scaffold shadcn. `destructive` é a única exceção: cor funcional (erro/perigo), não
 * expressão de marca, inalterada nos dois temas.
 * `panel`/`sunken`/`t2`/`t3`/`border2`/`redbg`/`amber`/`green` são tokens finos
 * adicionados no Milestone 7 (redesign, ADR-044) — valores hexadecimais literais
 * especificados pelo handoff de design, não derivados da rampa ink/paper.
 */
export const colorTokens = [
  "background",
  "foreground",
  "card",
  "card-foreground",
  "popover",
  "popover-foreground",
  "primary",
  "primary-foreground",
  "secondary",
  "secondary-foreground",
  "muted",
  "muted-foreground",
  "accent",
  "accent-foreground",
  "destructive",
  "border",
  "input",
  "ring",
  "sidebar",
  "sidebar-foreground",
  "sidebar-primary",
  "sidebar-primary-foreground",
  "sidebar-accent",
  "sidebar-accent-foreground",
  "sidebar-border",
  "sidebar-ring",
  "panel",
  "sunken",
  "t2",
  "t3",
  "border2",
  "redbg",
  "amber",
  "green",
] as const;

export type ColorToken = (typeof colorTokens)[number];
