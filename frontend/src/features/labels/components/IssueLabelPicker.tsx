import { Tag } from "lucide-react";

import { Button } from "@/shared/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from "@/shared/components/ui/dropdown-menu";

import { useAddIssueLabel, useIssueLabels, useLabels, useRemoveIssueLabel } from "../hooks";
import { LabelBadge } from "./LabelBadge";

export function IssueLabelPicker({
  workspaceId,
  issueId,
}: {
  workspaceId: string;
  issueId: string;
}) {
  const { data: allLabels } = useLabels(workspaceId);
  const { data: appliedLabels } = useIssueLabels(workspaceId, issueId);
  const addLabel = useAddIssueLabel(workspaceId, issueId);
  const removeLabel = useRemoveIssueLabel(workspaceId, issueId);

  const appliedIds = new Set((appliedLabels ?? []).map((label) => label.id));

  function toggle(labelId: string, isApplied: boolean) {
    if (isApplied) {
      removeLabel.mutate(labelId);
    } else {
      addLabel.mutate(labelId);
    }
  }

  return (
    <div className="flex flex-wrap items-center gap-1.5">
      {(appliedLabels ?? []).map((label) => (
        <LabelBadge key={label.id} label={label} />
      ))}

      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="ghost" size="icon-sm" aria-label="Gerenciar labels">
            <Tag />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="start">
          {!allLabels || allLabels.length === 0 ? (
            <p className="px-1.5 py-1 text-sm text-muted-foreground">Nenhuma label criada.</p>
          ) : (
            allLabels.map((label) => {
              const isApplied = appliedIds.has(label.id);
              return (
                <DropdownMenuCheckboxItem
                  key={label.id}
                  checked={isApplied}
                  onSelect={(event) => event.preventDefault()}
                  onCheckedChange={() => toggle(label.id, isApplied)}
                >
                  <span
                    className="inline-block size-2 shrink-0 rounded-full"
                    style={{ backgroundColor: label.color }}
                  />
                  {label.name}
                </DropdownMenuCheckboxItem>
              );
            })
          )}
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  );
}
