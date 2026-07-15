/** Famílias de fonte definidas em `src/index.css` (`--font-sans`/`--font-heading`). */
export const fontTokens = {
  sans: "var(--font-sans)",
  heading: "var(--font-heading)",
} as const;

export type FontToken = keyof typeof fontTokens;
