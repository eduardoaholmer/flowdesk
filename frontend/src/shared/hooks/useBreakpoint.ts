import { useMediaQuery } from "@/shared/hooks/useMediaQuery";

/** Espelha a escala default do Tailwind (`sm`/`md`/`lg`/`xl`/`2xl`) — não uma escala nova. */
const BREAKPOINTS = {
  sm: 640,
  md: 768,
  lg: 1024,
  xl: 1280,
  "2xl": 1536,
} as const;

export type Breakpoint = keyof typeof BREAKPOINTS;

/** `true` quando o viewport é maior ou igual ao breakpoint informado (mobile-first, como o Tailwind). */
export function useBreakpoint(breakpoint: Breakpoint): boolean {
  return useMediaQuery(`(min-width: ${BREAKPOINTS[breakpoint]}px)`);
}
