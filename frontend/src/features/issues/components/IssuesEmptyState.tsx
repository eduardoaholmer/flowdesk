import { ListTodo } from "lucide-react";

import { EmptyState } from "@/shared/components/feedback/EmptyState";
import { Button } from "@/shared/components/ui/button";
import { useUiStore } from "@/shared/stores/uiStore";

export function IssuesEmptyState({ hasFilters }: { hasFilters: boolean }) {
  const setCreateIssueOpen = useUiStore((state) => state.setCreateIssueOpen);

  return (
    <EmptyState
      icon={ListTodo}
      title={hasFilters ? "Nenhuma issue encontrada" : "Nenhuma issue ainda"}
      description={
        hasFilters ? "Ajuste a busca ou os filtros." : "Crie a primeira issue deste workspace."
      }
      action={!hasFilters && <Button onClick={() => setCreateIssueOpen(true)}>Nova issue</Button>}
    />
  );
}
