import type { WorkflowStateCategory } from "./types";

/** Rótulo + ordem de exibição da categoria no formulário de criar/editar status —
 * a categoria é semântica (usada por `ProjectRepository.issue_counts` no backend
 * para saber o que conta como concluído/cancelado), não o nome customizável. */
export const WORKFLOW_STATE_CATEGORY_LABELS: Record<WorkflowStateCategory, string> = {
  BACKLOG: "Backlog",
  UNSTARTED: "Não iniciado",
  STARTED: "Em andamento",
  COMPLETED: "Concluído",
  CANCELED: "Cancelado",
};

export const WORKFLOW_STATE_CATEGORY_ORDER: WorkflowStateCategory[] = [
  "BACKLOG",
  "UNSTARTED",
  "STARTED",
  "COMPLETED",
  "CANCELED",
];
