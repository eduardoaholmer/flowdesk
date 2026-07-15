import { motion, useReducedMotion } from "framer-motion";
import type { ReactNode } from "react";

import { scaleInVariants } from "./variants";

interface MotionWrapperProps {
  children: ReactNode;
  className?: string;
  delay?: number;
  /** `true` dentro de um `StaggerContainer` — ver `FadeIn.tsx` para o racional completo. */
  inherit?: boolean;
}

/** Entrada com leve zoom-in — para elementos que "aparecem" (badge novo, ícone de confirmação). */
export function ScaleIn({ children, className, delay = 0, inherit = false }: MotionWrapperProps) {
  const shouldReduceMotion = useReducedMotion();
  return (
    <motion.div
      initial={inherit ? undefined : "hidden"}
      animate={inherit ? undefined : "visible"}
      variants={scaleInVariants(Boolean(shouldReduceMotion))}
      transition={{ delay }}
      className={className}
    >
      {children}
    </motion.div>
  );
}
