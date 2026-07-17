/**
 * Única fonte de verdade para os paths de rota com escopo de workspace —
 * `router.tsx` usa `routePatterns` para declarar rotas, todo o resto usa
 * `workspaceRoutes` para construir links/navegação. Antes desta sprint os dois
 * lados eram template literals soltos e independentes em ~12 arquivos.
 */
export const routePatterns = {
  issues: "/w/:workspaceSlug/issues",
  issueDetail: "/w/:workspaceSlug/issues/:issueId",
  projects: "/w/:workspaceSlug/projects",
  projectDetail: "/w/:workspaceSlug/projects/:projectId",
  labels: "/w/:workspaceSlug/labels",
  settings: "/w/:workspaceSlug/settings",
  invitationAccept: "/invitations/:token/accept",
} as const;

export const workspaceRoutes = {
  issues: (workspaceSlug: string) => `/w/${workspaceSlug}/issues`,
  issueDetail: (workspaceSlug: string, issueId: string) => `/w/${workspaceSlug}/issues/${issueId}`,
  projects: (workspaceSlug: string) => `/w/${workspaceSlug}/projects`,
  projectDetail: (workspaceSlug: string, projectId: string) =>
    `/w/${workspaceSlug}/projects/${projectId}`,
  labels: (workspaceSlug: string) => `/w/${workspaceSlug}/labels`,
  settings: (workspaceSlug: string) => `/w/${workspaceSlug}/settings`,
} as const;

export function invitationAcceptRoute(token: string): string {
  return `/invitations/${token}/accept`;
}
