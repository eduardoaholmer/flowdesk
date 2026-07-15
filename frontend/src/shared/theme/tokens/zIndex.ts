/**
 * Escala de z-index para overlays customizados do app (Sidebar mobile drawer, Topbar
 * sticky) — não para primitivas Radix/shadcn (Dialog/Popover/DropdownMenu/Sheet), que
 * gerenciam seu próprio empilhamento via portal e já funcionam corretamente sem isto.
 * `layers` são os mesmos valores com nome semântico, para não espalhar números mágicos
 * pelo código quando o "porquê" de um valor importa mais que o número em si.
 */
export const zIndexTokens = {
  dropdown: 20,
  sticky: 30,
  overlay: 40,
  modal: 50,
  popover: 60,
  toast: 70,
} as const;

export const layers = zIndexTokens;

export type ZIndexLayer = keyof typeof zIndexTokens;
