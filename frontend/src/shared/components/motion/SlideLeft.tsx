import { motion, useReducedMotion } from "framer-motion";
import type { ReactNode } from "react";

import { slideLeftVariants } from "./variants";

interface MotionWrapperProps {
  children: ReactNode;
  className?: string;
  delay?: number;
  /** `true` dentro de um `StaggerContainer` — ver `FadeIn.tsx` para o racional completo. */
  inherit?: boolean;
}

/** Desliza da direita para a esquerda até a posição final — ex.: painel lateral entrando. */
export function SlideLeft({ children, className, delay = 0, inherit = false }: MotionWrapperProps) {
  const shouldReduceMotion = useReducedMotion();
  return (
    <motion.div
      initial={inherit ? undefined : "hidden"}
      animate={inherit ? undefined : "visible"}
      variants={slideLeftVariants(Boolean(shouldReduceMotion))}
      transition={{ delay }}
      className={className}
    >
      {children}
    </motion.div>
  );
}
