import { ErrorState } from "@/shared/components/feedback/ErrorState";
import { ListSkeleton } from "@/shared/components/skeletons/ListSkeleton";

import { useWorkflowStates } from "../hooks";
import { CreateWorkflowStateDialog } from "./CreateWorkflowStateDialog";
import { WorkflowStatesTable } from "./WorkflowStatesTable";

export function WorkflowStatesSettings({ workspaceId }: { workspaceId: string }) {
  const { data, isLoading, isError, refetch } = useWorkflowStates(workspaceId);

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between gap-3">
        <p className="text-sm text-t2">
          Status usados pelas issues e pelo board deste workspace. A ordem abaixo é a ordem das
          colunas do board.
        </p>
        <CreateWorkflowStateDialog workspaceId={workspaceId} />
      </div>

      {isLoading ? (
        <ListSkeleton rows={5} />
      ) : isError || !data ? (
        <ErrorState message="Não foi possível carregar os status." onRetry={() => refetch()} />
      ) : (
        <WorkflowStatesTable workspaceId={workspaceId} workflowStates={data} />
      )}
    </div>
  );
}
