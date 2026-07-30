import type { OverridableRole } from "./types";

/** Rótulo curto por permissão — mesmo catálogo de `docs/07-security.md` §8.2,
 * sem as 3 `LOCKED_PERMISSIONS` (nunca aparecem na matriz, o backend nunca as
 * devolve). Chave é a string crua (`"<domínio>.<ação>"`) devolvida pela API —
 * sem enum espelhado no frontend, já que a lista é só de exibição. */
export const PERMISSION_LABELS: Record<string, string> = {
  "workspace.view": "Ver workspace",
  "workspace.update": "Editar workspace",
  "workspace.invite": "Convidar membros",
  "member.remove": "Remover membro",
  "member.update_role": "Alterar papel de membro",
  "project.create": "Criar projeto",
  "project.read": "Ver projetos",
  "project.update": "Editar projeto",
  "project.delete": "Excluir projeto",
  "issue.create": "Criar issue",
  "issue.read": "Ver issues",
  "issue.update": "Editar issue",
  "issue.delete": "Excluir issue",
  "issue.assign": "Atribuir issue",
  "issue.change_status": "Mudar status de issue",
  "comment.create": "Comentar",
  "comment.update": "Editar comentário",
  "comment.delete": "Excluir comentário",
  "label.create": "Criar label",
  "label.read": "Ver labels",
  "label.update": "Editar label",
  "label.delete": "Excluir label",
  "attachment.create": "Anexar arquivo",
  "attachment.delete": "Excluir anexo",
  "workflow_state.read": "Ver status",
  "workflow_state.manage": "Gerenciar status",
};

/** Domínio (prefixo antes do ".") → rótulo do grupo + ordem de exibição —
 * mesma ordem de `docs/07-security.md` §8.2. */
export const PERMISSION_DOMAIN_LABELS: Record<string, string> = {
  workspace: "Workspace",
  member: "Membros",
  project: "Projetos",
  issue: "Issues",
  comment: "Comentários",
  label: "Labels",
  attachment: "Anexos",
  workflow_state: "Status de Issue",
};

export const PERMISSION_DOMAIN_ORDER = [
  "workspace",
  "member",
  "project",
  "issue",
  "comment",
  "label",
  "attachment",
  "workflow_state",
];

export function permissionDomain(permission: string): string {
  return permission.split(".")[0] ?? permission;
}

export const OVERRIDABLE_ROLE_ORDER: OverridableRole[] = ["ADMIN", "MEMBER", "GUEST"];

export const OVERRIDABLE_ROLE_LABELS: Record<OverridableRole, string> = {
  ADMIN: "Admin",
  MEMBER: "Membro",
  GUEST: "Convidado",
};
