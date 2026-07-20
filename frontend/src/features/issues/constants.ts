import type { IssueStatus } from "./types";

/** Única fonte de verdade para o rótulo de cada status — reusada por
 * `IssueStatusBadge` e pelo board (`IssuesBoardView`, cabeçalhos de coluna).
 * Ordem é também a ordem de exibição das colunas do board. */
export const ISSUE_STATUS_LABELS: Record<IssueStatus, string> = {
  BACKLOG: "Backlog",
  TODO: "Todo",
  IN_PROGRESS: "In Progress",
  IN_REVIEW: "In Review",
  DONE: "Done",
  CANCELED: "Canceled",
};
