import { motion, useReducedMotion } from "framer-motion";
import type { ReactNode } from "react";

import { slideRightVariants } from "./variants";

interface MotionWrapperProps {
  children: ReactNode;
  className?: string;
  delay?: number;
  /** `true` dentro de um `StaggerContainer` — ver `FadeIn.tsx` para o racional completo. */
  inherit?: boolean;
}

/** Desliza da esquerda para a direita até a posição final. */
export function SlideRight({
  children,
  className,
  delay = 0,
  inherit = false,
}: MotionWrapperProps) {
  const shouldReduceMotion = useReducedMotion();
  return (
    <motion.div
      initial={inherit ? undefined : "hidden"}
      animate={inherit ? undefined : "visible"}
      variants={slideRightVariants(Boolean(shouldReduceMotion))}
      transition={{ delay }}
      className={className}
    >
      {children}
    </motion.div>
  );
}
