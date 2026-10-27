import type { IssuePriority } from "./types";

/** Pontos de estimativa disponíveis no rail de detalhe da issue (Sprint 18.3, M7) —
 * mesma escala fixa do handoff de redesign, não configurável por workspace. */
export const ISSUE_ESTIMATE_OPTIONS = [1, 2, 3, 5, 8] as const;

/** Única fonte de verdade para o rótulo de cada prioridade — extraída na Sprint 18.4
 * (M7) ao virar a 4ª cópia local (`IssuePriorityBadge`, `IssueDetailRail`, `IssuesTable`),
 * cruzando o limiar que a própria ADR-046 já previa ("se uma quarta cópia aparecer, vale extrair"). */
export const ISSUE_PRIORITY_LABELS: Record<IssuePriority, string> = {
  NO_PRIORITY: "No priority",
  LOW: "Low",
  MEDIUM: "Medium",
  HIGH: "High",
  URGENT: "Urgent",
};
