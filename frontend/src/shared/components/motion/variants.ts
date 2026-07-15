import type { Transition, Variants } from "framer-motion";

import { motionDurationSeconds, motionEasing } from "@/shared/theme/tokens/motion";

/**
 * Transição base de todo wrapper de `shared/components/motion/` — duração `0` quando
 * o usuário prefere movimento reduzido (não só "mais rápido": sem transform nenhum),
 * nunca hardcoded por componente.
 */
export function buildTransition(
  shouldReduceMotion: boolean,
  duration = motionDurationSeconds.base,
): Transition {
  return {
    duration: shouldReduceMotion ? 0 : duration,
    ease: motionEasing.standard as unknown as Transition["ease"],
  };
}

const OFFSET_PX = 8;

export function fadeVariants(shouldReduceMotion: boolean): Variants {
  return {
    hidden: { opacity: 0 },
    visible: { opacity: 1, transition: buildTransition(shouldReduceMotion) },
  };
}

export function fadeUpVariants(shouldReduceMotion: boolean): Variants {
  return {
    hidden: { opacity: 0, y: shouldReduceMotion ? 0 : OFFSET_PX },
    visible: { opacity: 1, y: 0, transition: buildTransition(shouldReduceMotion) },
  };
}

export function fadeDownVariants(shouldReduceMotion: boolean): Variants {
  return {
    hidden: { opacity: 0, y: shouldReduceMotion ? 0 : -OFFSET_PX },
    visible: { opacity: 1, y: 0, transition: buildTransition(shouldReduceMotion) },
  };
}

export function scaleInVariants(shouldReduceMotion: boolean): Variants {
  return {
    hidden: { opacity: 0, scale: shouldReduceMotion ? 1 : 0.96 },
    visible: { opacity: 1, scale: 1, transition: buildTransition(shouldReduceMotion) },
  };
}

export function slideLeftVariants(shouldReduceMotion: boolean): Variants {
  return {
    hidden: { opacity: 0, x: shouldReduceMotion ? 0 : OFFSET_PX * 2 },
    visible: { opacity: 1, x: 0, transition: buildTransition(shouldReduceMotion) },
  };
}

export function slideRightVariants(shouldReduceMotion: boolean): Variants {
  return {
    hidden: { opacity: 0, x: shouldReduceMotion ? 0 : -OFFSET_PX * 2 },
    visible: { opacity: 1, x: 0, transition: buildTransition(shouldReduceMotion) },
  };
}

export const staggerContainerVariants: Variants = {
  hidden: {},
  visible: {
    transition: { staggerChildren: 0.05 },
  },
};
