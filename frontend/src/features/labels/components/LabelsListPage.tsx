import { Tag } from "lucide-react";

import { EmptyState } from "@/shared/components/feedback/EmptyState";
import { ErrorState } from "@/shared/components/feedback/ErrorState";
import { ListSkeleton } from "@/shared/components/skeletons/ListSkeleton";

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
        <ListSkeleton rows={3} />
      ) : isError ? (
        <ErrorState message="Não foi possível carregar as labels." onRetry={() => refetch()} />
      ) : labels && labels.length > 0 ? (
        <LabelsTable workspaceId={workspaceId} labels={labels} />
      ) : (
        <EmptyState
          icon={Tag}
          title="Nenhuma label ainda"
          description="Crie a primeira label deste workspace."
        />
      )}
    </div>
  );
}
