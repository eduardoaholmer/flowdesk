import { httpClient } from "@/shared/lib/httpClient";
import type { DataEnvelope } from "@/shared/lib/apiTypes";

import type { Workspace } from "./types";

export async function createWorkspace(name: string): Promise<Workspace> {
  const { data } = await httpClient.post<DataEnvelope<Workspace>>("/workspaces", { name });
  return data.data;
}
