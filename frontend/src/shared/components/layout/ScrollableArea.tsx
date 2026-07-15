import type { ReactNode } from "react";

import { ScrollArea } from "@/shared/components/ui/scroll-area";
import { cn } from "@/shared/lib/utils";

interface ScrollableAreaProps {
  children: ReactNode;
  /** Altura máxima antes de rolar — Tailwind arbitrary value, ex. `"24rem"`. */
  maxHeight?: string;
  className?: string;
}

/**
 * Convenience wrapper sobre `ui/scroll-area` (Radix) com um `maxHeight` já aplicado —
 * o primitivo por si só não define altura, então todo consumidor reimplementaria o
 * mesmo `style`/classe. Painéis longos (comentários, atividade, dropdown de busca)
 * usam este componente em vez do primitivo cru.
 */
export function ScrollableArea({ children, maxHeight = "24rem", className }: ScrollableAreaProps) {
  return (
    <ScrollArea className={cn(className)} style={{ maxHeight }}>
      {children}
    </ScrollArea>
  );
}
