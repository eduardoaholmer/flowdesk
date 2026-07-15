import { motion, useReducedMotion } from "framer-motion";
import type { ReactNode } from "react";

import { motionDurationSeconds } from "@/shared/theme/tokens/motion";

interface MotionCardProps {
  children: ReactNode;
  className?: string;
  onClick?: () => void;
}

/**
 * Card com leve resposta a hover/tap (não uma entrada de página — ver `FadeUp`/
 * `ScaleIn` para isso). Pensado para cards clicáveis (ex.: um `StatCard` que navega
 * para o detalhe). `whileHover`/`whileTap` já são no-op sob `prefers-reduced-motion`
 * — omitidos inteiramente nesse caso, não só acelerados.
 */
export function MotionCard({ children, className, onClick }: MotionCardProps) {
  const shouldReduceMotion = useReducedMotion();

  return (
    <motion.div
      className={className}
      onClick={onClick}
      whileHover={shouldReduceMotion ? undefined : { scale: 1.01 }}
      whileTap={shouldReduceMotion ? undefined : { scale: 0.99 }}
      transition={{ duration: motionDurationSeconds.fast }}
    >
      {children}
    </motion.div>
  );
}
