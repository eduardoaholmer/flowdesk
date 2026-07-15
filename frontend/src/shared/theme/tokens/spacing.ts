/** Escala default do Tailwind (base 4px) — já em uso em todo o projeto, não redefinida aqui. */
export const spacingScale = [0, 1, 2, 3, 4, 5, 6, 8, 10, 12, 16, 20, 24, 32] as const;

export type SpacingStep = (typeof spacingScale)[number];
