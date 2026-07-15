/**
 * Espelha a escala default do Tailwind (`sm`/`md`/`lg`/`xl`/`2xl`) — não uma escala
 * nova. Fonte de verdade para `shared/hooks/useBreakpoint.ts`, que antes hardcodava
 * este mesmo mapa localmente.
 */
export const breakpointTokens = {
  sm: 640,
  md: 768,
  lg: 1024,
  xl: 1280,
  "2xl": 1536,
} as const;

export type Breakpoint = keyof typeof breakpointTokens;
