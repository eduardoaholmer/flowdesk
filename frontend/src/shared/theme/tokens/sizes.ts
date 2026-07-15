/**
 * Classes de tamanho Tailwind (`size-*`, `width`+`height` combinados) já em uso para
 * ícone/avatar/controle no projeto hoje, do menor ao maior — não uma escala nova.
 */
export const sizeTokens = [
  "size-2",
  "size-3",
  "size-4",
  "size-5",
  "size-6",
  "size-7",
  "size-8",
  "size-9",
  "size-10",
] as const;

export type SizeToken = (typeof sizeTokens)[number];
