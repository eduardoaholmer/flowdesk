import { useIssues } from "@/features/issues/hooks";
import { useWorkflowStates } from "@/features/workflow-states/hooks";

const RADAR_PAGE_SIZE = 20;
const RADAR_LIMIT = 6;
/** "No radar" = ainda não concluído nem cancelado — categorias, não nomes
 * customizáveis de status (Sprint 9.2/ADR-056). */
const RADAR_CATEGORIES = new Set(["BACKLOG", "UNSTARTED", "STARTED"]);

/**
 * Issues "no radar" do usuário atual (atribuídas a ele, ainda não concluídas/canceladas),
 * ordenadas por prioridade — mesma fonte usada pelo widget "Minhas issues" e pelo resumo
 * textual do cabeçalho do Início (M7, Sprint 18.5). `IssueListParams` só aceita um único
 * `status_id`, então o filtro por categoria é feito aqui, client-side, sobre uma página um
 * pouco maior que o limite exibido — mesma decisão de não estender o contrato de filtro por
 * uma única tela (ver ADR-045/046).
 */
export function useMyRadarIssues(workspaceId: string, userId: string) {
  const { data, isLoading, isError, refetch } = useIssues(workspaceId, {
    page: 1,
    per_page: RADAR_PAGE_SIZE,
    assignee_id: userId,
    sort: "-priority",
  });
  const { data: workflowStates } = useWorkflowStates(workspaceId);
  const workflowStateById = new Map((workflowStates ?? []).map((state) => [state.id, state]));

  const issues = (data?.data ?? [])
    .filter((issue) => {
      const category = workflowStateById.get(issue.status_id)?.category;
      return category ? RADAR_CATEGORIES.has(category) : false;
    })
    .slice(0, RADAR_LIMIT);
  const inProgressCount = issues.filter(
    (issue) => workflowStateById.get(issue.status_id)?.category === "STARTED",
  ).length;
  const queuedCount = issues.length - inProgressCount;

  return {
    issues,
    workflowStateById,
    inProgressCount,
    queuedCount,
    isLoading,
    isError,
    refetch,
  };
}
