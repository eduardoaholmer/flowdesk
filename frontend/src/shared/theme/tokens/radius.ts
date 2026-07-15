/** Escala de raio já mapeada em `src/index.css` (`--radius-*`, derivada de `--radius`). */
export const radiusTokens = ["sm", "md", "lg", "xl", "2xl", "3xl", "4xl"] as const;

export type RadiusToken = (typeof radiusTokens)[number];
