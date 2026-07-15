import { motion } from "framer-motion";
import type { ReactNode } from "react";

import { staggerContainerVariants } from "./variants";

interface StaggerContainerProps {
  children: ReactNode;
  className?: string;
}

/**
 * Orquestra a entrada de múltiplos filhos em sequência (cada filho precisa ser um
 * `motion.*`/wrapper deste mesmo módulo com `variants` — ex.: vários `FadeUp` numa
 * lista) — sem isto, todos os itens de uma lista animariam ao mesmo tempo.
 */
export function StaggerContainer({ children, className }: StaggerContainerProps) {
  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={staggerContainerVariants}
      className={className}
    >
      {children}
    </motion.div>
  );
}
