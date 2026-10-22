import { Check, Copy } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { useWorkflowStates } from "@/features/workflow-states/hooks";
import { Button } from "@/shared/components/ui/button";

import { ISSUE_PRIORITY_LABELS } from "../constants";
import type { Issue } from "../types";

function formatIssueSection(issue: Issue, statusName: string, heading: string): string {
  const lines = [
    heading,
    "",
    `Status: ${statusName} · Prioridade: ${ISSUE_PRIORITY_LABELS[issue.priority]}`,
    "",
    issue.description || "Sem descrição.",
  ];
  return lines.join("\n");
}

function buildPrompt(issue: Issue, subIssues: Issue[], statusNameById: Map<string, string>): string {
  const statusName = (id: string) => statusNameById.get(id) ?? "—";

  const sections = [
    formatIssueSection(issue, statusName(issue.status_id), `# [${issue.identifier}] ${issue.title}`),
  ];

  if (subIssues.length === 0) {
    sections.push(`## Sub-issues\n\nSem sub-issues.`);
  } else {
    const subSections = subIssues.map((subIssue) =>
      formatIssueSection(
        subIssue,
        statusName(subIssue.status_id),
        `### [${subIssue.identifier}] ${subIssue.title}`,
      ),
    );
    sections.push([`## Sub-issues (${subIssues.length})`, ...subSections].join("\n\n"));
  }

  return sections.join("\n\n");
}

export function CopyIssuePromptButton({
  workspaceId,
  issue,
  subIssues,
}: {
  workspaceId: string;
  issue: Issue;
  subIssues: Issue[];
}) {
  const [copied, setCopied] = useState(false);
  const { data: workflowStates } = useWorkflowStates(workspaceId);

  async function handleCopy() {
    const statusNameById = new Map((workflowStates ?? []).map((state) => [state.id, state.name]));
    const prompt = buildPrompt(issue, subIssues, statusNameById);
    try {
      await navigator.clipboard.writeText(prompt);
      setCopied(true);
      toast.success("Prompt copiado.");
      setTimeout(() => setCopied(false), 1500);
    } catch {
      toast.error("Não foi possível copiar o prompt.");
    }
  }

  return (
    <Button variant="ghost" size="icon-sm" aria-label="Copiar prompt da issue" onClick={handleCopy}>
      {copied ? <Check /> : <Copy />}
    </Button>
  );
}
