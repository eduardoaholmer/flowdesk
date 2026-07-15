import { motion, useReducedMotion } from "framer-motion";
import type { ReactNode } from "react";

import { fadeVariants } from "./variants";

interface MotionWrapperProps {
  children: ReactNode;
  className?: string;
  delay?: number;
  /**
   * `true` quando usado dentro de um `StaggerContainer` — omite `initial`/`animate`
   * próprios para herdar o estado do ancestral (é isso que faz o stagger funcionar;
   * um filho com `animate` explícito próprio ignora a orquestração do pai). Falso
   * (padrão) para uso standalone, animando sozinho ao montar.
   */
  inherit?: boolean;
}

/** Fade discreto de entrada — respeita `prefers-reduced-motion` via `useReducedMotion()`. */
export function FadeIn({ children, className, delay = 0, inherit = false }: MotionWrapperProps) {
  const shouldReduceMotion = useReducedMotion();
  return (
    <motion.div
      initial={inherit ? undefined : "hidden"}
      animate={inherit ? undefined : "visible"}
      variants={fadeVariants(Boolean(shouldReduceMotion))}
      transition={{ delay }}
      className={className}
    >
      {children}
    </motion.div>
  );
}
