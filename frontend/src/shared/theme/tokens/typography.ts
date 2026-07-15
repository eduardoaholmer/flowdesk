/** Classes de tamanho de texto Tailwind já usadas no projeto, do menor ao maior. */
export const typographyScale = [
  "text-xs",
  "text-sm",
  "text-base",
  "text-lg",
  "text-xl",
  "text-2xl",
  "text-4xl",
] as const;

export type TypographyStep = (typeof typographyScale)[number];
