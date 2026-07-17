/**
 * Motion — os valores em `--duration-*`/`--ease-*` vivem em `src/index.css`; aqui só
 * tipamos para consumo em contexto JS (ex.: coordenar um `setTimeout` com a duração de
 * uma transição CSS). O motion system do projeto é inteiramente CSS (`transition-*`,
 * `data-state` do Radix + `tw-animate-css`) — não framer-motion, removido no
 * Milestone 3 por ter zero call site real após uma sprint inteira de oportunidade de
 * adoção (`docs/09-decision-log.md` ADR-019). CSS-only também é a escolha certa para
 * "prioritize speed": sem JS de animação no caminho crítico de abrir um dropdown/modal.
 */
export const motionTokens = {
  duration: {
    fast: "var(--duration-fast)",
    base: "var(--duration-base)",
    slow: "var(--duration-slow)",
  },
  easing: {
    standard: "var(--ease-standard)",
    emphasized: "var(--ease-emphasized)",
  },
} as const;
