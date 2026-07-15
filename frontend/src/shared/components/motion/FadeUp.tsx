import { motion, useReducedMotion } from "framer-motion";
import type { ReactNode } from "react";

import { fadeUpVariants } from "./variants";

interface MotionWrapperProps {
  children: ReactNode;
  className?: string;
  delay?: number;
  /** `true` dentro de um `StaggerContainer` — ver `FadeIn.tsx` para o racional completo. */
  inherit?: boolean;
}

/** Entra de baixo para cima, com fade — o wrapper de entrada mais comum para cards/linhas de lista. */
export function FadeUp({ children, className, delay = 0, inherit = false }: MotionWrapperProps) {
  const shouldReduceMotion = useReducedMotion();
  return (
    <motion.div
      initial={inherit ? undefined : "hidden"}
      animate={inherit ? undefined : "visible"}
      variants={fadeUpVariants(Boolean(shouldReduceMotion))}
      transition={{ delay }}
      className={className}
    >
      {children}
    </motion.div>
  );
}
