import { ListTodo } from "lucide-react";

import { EmptyState } from "@/shared/components/EmptyState";

import { CreateIssueDialog } from "./CreateIssueDialog";

export function IssuesEmptyState({
  workspaceId,
  hasFilters,
}: {
  workspaceId: string;
  hasFilters: boolean;
}) {
  return (
    <EmptyState
      icon={ListTodo}
      title={hasFilters ? "Nenhuma issue encontrada" : "Nenhuma issue ainda"}
      description={
        hasFilters ? "Ajuste a busca ou os filtros." : "Crie a primeira issue deste workspace."
      }
      action={!hasFilters && <CreateIssueDialog workspaceId={workspaceId} />}
    />
  );
}
