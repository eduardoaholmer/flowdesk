import type { WorkspaceRole } from "@/features/workspaces/types";

/** Papel exclui `OWNER` — nunca é customizável, sempre tem toda permissão. */
export type OverridableRole = Exclude<WorkspaceRole, "OWNER">;

export interface PermissionMatrixEntry {
  permission: string;
  role: OverridableRole;
  default: boolean;
  effective: boolean;
  is_override: boolean;
}

export interface PermissionOverrideUpsertInput {
  role: OverridableRole;
  permission: string;
  granted: boolean;
}
