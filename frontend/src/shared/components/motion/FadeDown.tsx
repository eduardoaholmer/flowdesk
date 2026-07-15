import { motion, useReducedMotion } from "framer-motion";
import type { ReactNode } from "react";

import { fadeDownVariants } from "./variants";

interface MotionWrapperProps {
  children: ReactNode;
  className?: string;
  delay?: number;
  /** `true` dentro de um `StaggerContainer` — ver `FadeIn.tsx` para o racional completo. */
  inherit?: boolean;
}

/** Entra de cima para baixo, com fade — para elementos que "caem" no lugar (ex.: dropdown/tooltip customizado). */
export function FadeDown({ children, className, delay = 0, inherit = false }: MotionWrapperProps) {
  const shouldReduceMotion = useReducedMotion();
  return (
    <motion.div
      initial={inherit ? undefined : "hidden"}
      animate={inherit ? undefined : "visible"}
      variants={fadeDownVariants(Boolean(shouldReduceMotion))}
      transition={{ delay }}
      className={className}
    >
      {children}
    </motion.div>
  );
}
