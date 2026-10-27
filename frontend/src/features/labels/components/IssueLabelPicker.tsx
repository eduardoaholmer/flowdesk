import { Tag } from "lucide-react";

import { Button } from "@/shared/components/ui/button";

import { useAddIssueLabel, useIssueLabels, useRemoveIssueLabel } from "../hooks";
import { LabelBadge } from "./LabelBadge";
import { LabelCombobox } from "./LabelCombobox";

export function IssueLabelPicker({
  workspaceId,
  issueId,
}: {
  workspaceId: string;
  issueId: string;
}) {
  const { data: appliedLabels } = useIssueLabels(workspaceId, issueId);
  const addLabel = useAddIssueLabel(workspaceId, issueId);
  const removeLabel = useRemoveIssueLabel(workspaceId, issueId);

  const appliedIds = new Set((appliedLabels ?? []).map((label) => label.id));

  return (
    <div className="flex flex-wrap items-center gap-1.5">
      {(appliedLabels ?? []).map((label) => (
        <LabelBadge key={label.id} label={label} />
      ))}

      <LabelCombobox
        workspaceId={workspaceId}
        selectedIds={appliedIds}
        onToggle={(label, selected) =>
          selected ? addLabel.mutate(label.id) : removeLabel.mutate(label.id)
        }
      >
        <Button variant="ghost" size="icon-sm" aria-label="Gerenciar labels">
          <Tag />
        </Button>
      </LabelCombobox>
    </div>
  );
}
