import { httpClient } from "@/shared/lib/httpClient";
import type { DataEnvelope } from "@/shared/lib/apiTypes";

import type { WorkflowState, WorkflowStateCreateInput, WorkflowStateUpdateInput } from "./types";

export async function listWorkflowStates(workspaceId: string): Promise<WorkflowState[]> {
  const { data } = await httpClient.get<DataEnvelope<WorkflowState[]>>(
    `/workspaces/${workspaceId}/workflow-states`,
  );
  return data.data;
}

export async function createWorkflowState(
  workspaceId: string,
  input: WorkflowStateCreateInput,
): Promise<WorkflowState> {
  const { data } = await httpClient.post<DataEnvelope<WorkflowState>>(
    `/workspaces/${workspaceId}/workflow-states`,
    input,
  );
  return data.data;
}

export async function updateWorkflowState(
  workspaceId: string,
  stateId: string,
  input: WorkflowStateUpdateInput,
): Promise<WorkflowState> {
  const { data } = await httpClient.patch<DataEnvelope<WorkflowState>>(
    `/workspaces/${workspaceId}/workflow-states/${stateId}`,
    input,
  );
  return data.data;
}

export async function deleteWorkflowState(
  workspaceId: string,
  stateId: string,
  reassignToId?: string,
): Promise<void> {
  await httpClient.delete(`/workspaces/${workspaceId}/workflow-states/${stateId}`, {
    params: reassignToId ? { reassign_to_id: reassignToId } : undefined,
  });
}

export async function reorderWorkflowStates(
  workspaceId: string,
  orderedIds: string[],
): Promise<WorkflowState[]> {
  const { data } = await httpClient.post<DataEnvelope<WorkflowState[]>>(
    `/workspaces/${workspaceId}/workflow-states/reorder`,
    { ordered_ids: orderedIds },
  );
  return data.data;
}
