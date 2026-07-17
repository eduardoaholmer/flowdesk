/**
 * Escala de opacidade já em uso no projeto (levantada do código real, não inventada —
 * mesmo critério de `sizeTokens`/`shadowScale`). Duas famílias distintas:
 * `opacity-*` (opacidade do próprio elemento) e modificadores alfa de cor (`/N`,
 * aplicados sobre um token de cor — ex.: `ring-ring/50`, `border-foreground/10`).
 */
export const opacityScale = {
  /** Estado desabilitado (`disabled:opacity-50`) — todo controle interativo do projeto. */
  disabled: "opacity-50",
  /** Dado obsoleto durante um refetch em segundo plano (`IssuesListPage`/`ProjectsListPage`). */
  stale: "opacity-60",
  /** Estado oculto de uma transição controlada por classe, não por `data-state` do Radix. */
  hidden: "opacity-0",
  visible: "opacity-100",
} as const;

/** Modificadores alfa (`/N`) aplicados sobre um token de cor — nunca uma cor nova. */
export const alphaScale = [10, 15, 20, 30, 40, 50, 80] as const;

export type OpacityToken = keyof typeof opacityScale;
export type AlphaStep = (typeof alphaScale)[number];
