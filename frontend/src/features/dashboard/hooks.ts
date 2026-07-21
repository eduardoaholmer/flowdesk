import { useIssues } from "@/features/issues/hooks";
import type { IssueStatus } from "@/features/issues/types";

const RADAR_PAGE_SIZE = 20;
const RADAR_STATUSES: IssueStatus[] = ["BACKLOG", "TODO", "IN_PROGRESS"];
const RADAR_LIMIT = 6;

/**
 * Issues "no radar" do usuário atual (atribuídas a ele, ainda não concluídas/canceladas
 * nem em revisão), ordenadas por prioridade — mesma fonte usada pelo widget "Minhas
 * issues" e pelo resumo textual do cabeçalho do Início (M7, Sprint 18.5). `IssueListParams`
 * só aceita um único `status`, então o filtro por múltiplos status é feito aqui,
 * client-side, sobre uma página um pouco maior que o limite exibido — mesma decisão
 * de não estender o contrato de filtro por uma única tela (ver ADR-045/046).
 */
export function useMyRadarIssues(workspaceId: string, userId: string) {
  const { data, isLoading, isError, refetch } = useIssues(workspaceId, {
    page: 1,
    per_page: RADAR_PAGE_SIZE,
    assignee_id: userId,
    sort: "-priority",
  });

  const issues = (data?.data ?? [])
    .filter((issue) => RADAR_STATUSES.includes(issue.status))
    .slice(0, RADAR_LIMIT);
  const inProgressCount = issues.filter((issue) => issue.status === "IN_PROGRESS").length;
  const queuedCount = issues.length - inProgressCount;

  return { issues, inProgressCount, queuedCount, isLoading, isError, refetch };
}
