/**
 * Motion — única categoria sem equivalente prévio no projeto antes da Sprint 8.5. Os
 * valores em `--duration-*`/`--ease-*` vivem em `src/index.css`; aqui só tipamos para
 * consumo em JS/className (`duration-[var(--duration-base)]`).
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

/**
 * Mesmas durações de `--duration-*` (100ms/150ms/250ms), espelhadas como segundos
 * numéricos — Framer Motion (`shared/components/motion/`) não lê custom properties CSS
 * como duração de transição, só números. Se `--duration-*` mudar em `index.css`, este
 * objeto precisa mudar junto (não há forma de derivar um número de uma CSS var em
 * tempo de build sem um passo de build adicional, o que seria over-engineering para o
 * ganho — CLAUDE.md §1.6).
 */
export const motionDurationSeconds = {
  fast: 0.1,
  base: 0.15,
  slow: 0.25,
} as const;

/** Mesmas curvas de `--ease-*`, como arrays `[x1, y1, x2, y2]` (formato que Framer Motion espera). */
export const motionEasing = {
  standard: [0.4, 0, 0.2, 1],
  emphasized: [0.2, 0, 0, 1],
} as const;
