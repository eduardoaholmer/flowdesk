import { motion, useReducedMotion } from "framer-motion";
import type { ReactNode } from "react";

import { scaleInVariants } from "./variants";

interface MotionModalProps {
  children: ReactNode;
  className?: string;
}

/**
 * Reveal de conteúdo **dentro** de um modal já aberto (ex.: trocar de etapa num
 * wizard, sem fechar/reabrir o `Dialog`) — não substitui a animação de abrir/fechar
 * do próprio `ui/dialog.tsx`/`ui/sheet.tsx` (já animada via `data-state` + classes
 * Tailwind do shadcn). Envolver o `DialogContent` inteiro com isto duplicaria a
 * animação de entrada (a do Radix + esta, ao mesmo tempo).
 */
export function MotionModal({ children, className }: MotionModalProps) {
  const shouldReduceMotion = useReducedMotion();
  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={scaleInVariants(Boolean(shouldReduceMotion))}
      className={className}
    >
      {children}
    </motion.div>
  );
}
