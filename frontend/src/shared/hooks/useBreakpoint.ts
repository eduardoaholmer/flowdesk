import { useMediaQuery } from "@/shared/hooks/useMediaQuery";
import { breakpointTokens, type Breakpoint } from "@/shared/theme/tokens/breakpoints";

export type { Breakpoint };

/** `true` quando o viewport é maior ou igual ao breakpoint informado (mobile-first, como o Tailwind). */
export function useBreakpoint(breakpoint: Breakpoint): boolean {
  return useMediaQuery(`(min-width: ${breakpointTokens[breakpoint]}px)`);
}
