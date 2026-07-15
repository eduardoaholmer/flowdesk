/**
 * Nomes dos tokens de cor semânticos definidos em `src/index.css` (`:root`/`.dark`).
 * Não redefine valores — a paleta é placeholder em tons de cinza (achromatic) até a
 * identidade visual definitiva ser aplicada; trocar a marca troca só os valores CSS,
 * nunca esta lista de nomes nem nenhum componente que a consome.
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
] as const;

export type ColorToken = (typeof colorTokens)[number];
