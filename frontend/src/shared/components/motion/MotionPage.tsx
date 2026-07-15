import { motion, useReducedMotion } from "framer-motion";
import type { ReactNode } from "react";

import { fadeUpVariants } from "./variants";

interface MotionPageProps {
  children: ReactNode;
  className?: string;
}

/**
 * Entrada discreta de conteúdo de página, para uma página envolver seu próprio
 * retorno com isto. Não coordena transição de **saída** entre rotas (exigiria
 * `AnimatePresence` no nível do `router.tsx`, decisão de arquitetura de roteamento
 * fora do escopo desta sprint — infraestrutura de motion, não uma mudança de
 * roteamento) — é só a entrada.
 */
export function MotionPage({ children, className }: MotionPageProps) {
  const shouldReduceMotion = useReducedMotion();
  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={fadeUpVariants(Boolean(shouldReduceMotion))}
      className={className}
    >
      {children}
    </motion.div>
  );
}
