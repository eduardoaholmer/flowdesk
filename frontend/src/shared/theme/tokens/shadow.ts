/** Classes de elevação Tailwind já usadas (Dialog/Sheet/Popover geram shadow-lg/shadow-md via shadcn). */
export const shadowScale = [
  "shadow-xs",
  "shadow-sm",
  "shadow-md",
  "shadow-lg",
  "shadow-xl",
] as const;

export type ShadowStep = (typeof shadowScale)[number];
