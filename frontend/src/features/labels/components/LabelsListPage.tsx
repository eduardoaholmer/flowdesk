import { ErrorState } from "@/shared/components/ErrorState";
import { Skeleton } from "@/shared/components/ui/skeleton";

import { useLabels } from "../hooks";
import { CreateLabelDialog } from "./CreateLabelDialog";
import { LabelsTable } from "./LabelsTable";

export function LabelsListPage({ workspaceId }: { workspaceId: string }) {
  const { data: labels, isLoading, isError, refetch } = useLabels(workspaceId);

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-lg font-semibold">Labels</h1>
          <p className="text-sm text-muted-foreground">
            Organize issues por categoria, área ou prioridade customizada.
          </p>
        </div>
        <CreateLabelDialog workspaceId={workspaceId} />
      </div>

      {isLoading ? (
        <div className="flex flex-col gap-2">
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-10 w-full" />
        </div>
      ) : isError ? (
        <ErrorState message="Não foi possível carregar as labels." onRetry={() => refetch()} />
      ) : labels && labels.length > 0 ? (
        <LabelsTable workspaceId={workspaceId} labels={labels} />
      ) : (
        <div className="rounded-xl border border-dashed p-8 text-center text-sm text-muted-foreground">
          Nenhuma label criada ainda.
        </div>
      )}
    </div>
  );
}
