/**
 * Referência tipada dos design tokens do FlowDesk. Não redefine nem inventa
 * valores — cada campo aponta para a fonte de verdade (CSS custom property em
 * `src/index.css` ou escala default do Tailwind já em uso no projeto). Existe
 * para dar aos componentes um ponto único de consulta em TS/JS (ex.: motion
 * usado fora de className, como duração de uma animação orquestrada em JS),
 * não para substituir classes utilitárias Tailwind no dia a dia.
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

export const radiusTokens = ["sm", "md", "lg", "xl", "2xl", "3xl", "4xl"] as const;

/** Escala default do Tailwind (base 4px) — já em uso em todo o projeto, não redefinida aqui. */
export const spacingScale = [0, 1, 2, 3, 4, 5, 6, 8, 10, 12, 16, 20, 24, 32] as const;

/** Classes de tamanho de texto Tailwind já usadas no projeto, do menor ao maior. */
export const typographyScale = [
  "text-xs",
  "text-sm",
  "text-base",
  "text-lg",
  "text-xl",
  "text-2xl",
  "text-4xl",
] as const;

/** Classes de elevação Tailwind já usadas (Dialog/Sheet/Popover geram shadow-lg/shadow-md via shadcn). */
export const shadowScale = [
  "shadow-xs",
  "shadow-sm",
  "shadow-md",
  "shadow-lg",
  "shadow-xl",
] as const;

/**
 * Motion — única categoria sem equivalente prévio no projeto. Os valores em
 * `--duration-*`/`--ease-*` vivem em `src/index.css`; aqui só tipamos para
 * consumo em JS (ex.: `setTimeout` sincronizado com uma transição CSS).
 * Em className, usar via arbitrary value: `duration-[var(--duration-base)]`.
 */
export const motionTokens = {
  duration: {
    fast: "var(--duration-fast)",
    base: "var(--duration-base)",
    slow: "var(--duration-slow)",
  },
  easing: {
    standard: "var(--ease-standard)",
    emphasized: "var(--ease-emphasized)",
  },
} as const;
