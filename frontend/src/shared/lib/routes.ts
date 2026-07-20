/**
 * Única fonte de verdade para os paths de rota com escopo de workspace —
 * `router.tsx` usa `routePatterns` para declarar rotas, todo o resto usa
 * `workspaceRoutes` para construir links/navegação. Antes desta sprint os dois
 * lados eram template literals soltos e independentes em ~12 arquivos.
 */
export const routePatterns = {
  workspaceHome: "/w/:workspaceSlug",
  issues: "/w/:workspaceSlug/issues",
  issueDetail: "/w/:workspaceSlug/issues/:issueId",
  board: "/w/:workspaceSlug/board",
  projects: "/w/:workspaceSlug/projects",
  projectDetail: "/w/:workspaceSlug/projects/:projectId",
  labels: "/w/:workspaceSlug/labels",
  settings: "/w/:workspaceSlug/settings",
  invitationAccept: "/invitations/:token/accept",
  resetPassword: "/reset-password/:token",
} as const;

export const workspaceRoutes = {
  home: (workspaceSlug: string) => `/w/${workspaceSlug}`,
  issues: (workspaceSlug: string) => `/w/${workspaceSlug}/issues`,
  issueDetail: (workspaceSlug: string, issueId: string) => `/w/${workspaceSlug}/issues/${issueId}`,
  board: (workspaceSlug: string) => `/w/${workspaceSlug}/board`,
  projects: (workspaceSlug: string) => `/w/${workspaceSlug}/projects`,
  projectDetail: (workspaceSlug: string, projectId: string) =>
    `/w/${workspaceSlug}/projects/${projectId}`,
  labels: (workspaceSlug: string) => `/w/${workspaceSlug}/labels`,
  settings: (workspaceSlug: string) => `/w/${workspaceSlug}/settings`,
} as const;

export function invitationAcceptRoute(token: string): string {
  return `/invitations/${token}/accept`;
}

export function resetPasswordRoute(token: string): string {
  return `/reset-password/${token}`;
}

interface LoginRedirectLocation {
  pathname: string;
  search: string;
}

/**
 * `RequireAuth` grava `state: { from: location }` ao redirecionar para `/login`
 * (ex.: alguém desconectado clica em um link de convite). Sem isso, todo login
 * caía sempre em `/` e o destino original era perdido silenciosamente.
 */
export function resolveLoginRedirect(state: unknown): string {
  const from = (state as { from?: LoginRedirectLocation } | null)?.from;
  if (!from) return "/";
  return `${from.pathname}${from.search}`;
}
