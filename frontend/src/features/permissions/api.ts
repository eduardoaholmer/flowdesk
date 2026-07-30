import { httpClient } from "@/shared/lib/httpClient";
import type { DataEnvelope } from "@/shared/lib/apiTypes";

import type { PermissionMatrixEntry, PermissionOverrideUpsertInput } from "./types";

export async function listPermissionMatrix(workspaceId: string): Promise<PermissionMatrixEntry[]> {
  const { data } = await httpClient.get<DataEnvelope<PermissionMatrixEntry[]>>(
    `/workspaces/${workspaceId}/permission-overrides`,
  );
  return data.data;
}

export async function setPermissionOverride(
  workspaceId: string,
  input: PermissionOverrideUpsertInput,
): Promise<PermissionMatrixEntry[]> {
  const { data } = await httpClient.put<DataEnvelope<PermissionMatrixEntry[]>>(
    `/workspaces/${workspaceId}/permission-overrides`,
    input,
  );
  return data.data;
}
