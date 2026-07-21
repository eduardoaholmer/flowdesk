import { Check, ChevronDown } from "lucide-react";
import type { ReactNode } from "react";

import { useProjects } from "@/features/projects/hooks";
import { useWorkspaceMembers } from "@/features/workspaces/hooks";
import { IssueLabelPicker } from "@/features/labels/components/IssueLabelPicker";
import { Avatar, AvatarFallback } from "@/shared/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/shared/components/ui/dropdown-menu";
import { MAX_PICKER_PAGE_SIZE } from "@/shared/lib/constants";
import { formatDate } from "@/shared/lib/date";
import { getInitials } from "@/shared/lib/string";
import { cn } from "@/shared/lib/utils";

import { useUpdateIssue } from "../hooks";
import { ISSUE_ESTIMATE_OPTIONS, ISSUE_PRIORITY_LABELS, ISSUE_STATUS_LABELS } from "../constants";
import type { Issue, IssuePriority, IssueStatus } from "../types";
import { IssuePriorityIcon } from "./IssuePriorityIcon";
import { IssueStatusIcon } from "./IssueStatusIcon";

const NONE = "__none__";

const STATUS_ORDER: IssueStatus[] = [
  "BACKLOG",
  "TODO",
  "IN_PROGRESS",
  "IN_REVIEW",
  "DONE",
  "CANCELED",
];

const PRIORITY_ORDER: IssuePriority[] = ["URGENT", "HIGH", "MEDIUM", "LOW", "NO_PRIORITY"];

function quickDueDate(daysFromNow: number): string {
  const date = new Date();
  date.setDate(date.getDate() + daysFromNow);
  return date.toISOString().slice(0, 10);
}

interface RailOption {
  key: string;
  label: string;
  icon?: ReactNode;
  checked: boolean;
  onSelect: () => void;
}

function RailField({
  label,
  icon,
  valueText,
  options,
}: {
  label: string;
  icon?: ReactNode;
  valueText: string;
  options: RailOption[];
}) {
  return (
    <div>
      <div className="mb-1 text-[10.5px] font-semibold tracking-wide text-t3 uppercase">
        {label}
      </div>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <button
            type="button"
            className="flex w-full items-center gap-2 rounded-md border border-transparent px-1.5 py-1 text-left text-[12.5px] font-medium hover:bg-sunken"
          >
            {icon}
            <span className="min-w-0 flex-1 truncate">{valueText}</span>
            <ChevronDown className="size-3 shrink-0 text-t3" />
          </button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="start" className="w-56">
          {options.map((option) => (
            <DropdownMenuItem key={option.key} onSelect={option.onSelect}>
              {option.icon}
              <span className="flex-1">{option.label}</span>
              {option.checked && <Check className="size-3.5" />}
            </DropdownMenuItem>
          ))}
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  );
}

function RailAvatarIcon({ name }: { name: string }) {
  return (
    <Avatar className="size-5 border border-border2 bg-sunken">
      <AvatarFallback className="bg-transparent text-[8px] font-semibold text-t2">
        {getInitials(name)}
      </AvatarFallback>
    </Avatar>
  );
}

export function IssueDetailRail({ workspaceId, issue }: { workspaceId: string; issue: Issue }) {
  const { data: members } = useWorkspaceMembers(workspaceId);
  const { data: projects } = useProjects(workspaceId, { page: 1, per_page: MAX_PICKER_PAGE_SIZE });
  const updateIssue = useUpdateIssue(workspaceId, issue.id);

  const assignee = members?.find((member) => member.user.id === issue.assignee_id)?.user;
  const project = projects?.data.find((p) => p.id === issue.project_id);

  return (
    <aside
      className={cn(
        "flex w-full shrink-0 flex-col gap-4 border-t pt-6 md:w-68 md:border-t-0 md:border-l md:pt-0 md:pl-5",
      )}
    >
      <RailField
        label="Status"
        icon={<IssueStatusIcon status={issue.status} />}
        valueText={ISSUE_STATUS_LABELS[issue.status]}
        options={STATUS_ORDER.map((status) => ({
          key: status,
          label: ISSUE_STATUS_LABELS[status],
          icon: <IssueStatusIcon status={status} />,
          checked: status === issue.status,
          onSelect: () => updateIssue.mutate({ status }),
        }))}
      />

      <RailField
        label="Prioridade"
        icon={<IssuePriorityIcon priority={issue.priority} />}
        valueText={ISSUE_PRIORITY_LABELS[issue.priority]}
        options={PRIORITY_ORDER.map((priority) => ({
          key: priority,
          label: ISSUE_PRIORITY_LABELS[priority],
          icon: <IssuePriorityIcon priority={priority} />,
          checked: priority === issue.priority,
          onSelect: () => updateIssue.mutate({ priority }),
        }))}
      />

      <RailField
        label="Responsável"
        icon={assignee ? <RailAvatarIcon name={assignee.name} /> : undefined}
        valueText={assignee?.name ?? "Sem responsável"}
        options={[
          {
            key: NONE,
            label: "Sem responsável",
            checked: !issue.assignee_id,
            onSelect: () => updateIssue.mutate({ assignee_id: undefined }),
          },
          ...(members ?? []).map((member) => ({
            key: member.user.id,
            label: member.user.name,
            icon: <RailAvatarIcon name={member.user.name} />,
            checked: member.user.id === issue.assignee_id,
            onSelect: () => updateIssue.mutate({ assignee_id: member.user.id }),
          })),
        ]}
      />

      <RailField
        label="Projeto"
        valueText={project?.name ?? "Sem projeto"}
        options={[
          {
            key: NONE,
            label: "Sem projeto",
            checked: !issue.project_id,
            onSelect: () => updateIssue.mutate({ project_id: undefined }),
          },
          ...(projects?.data ?? []).map((p) => ({
            key: p.id,
            label: p.name,
            checked: p.id === issue.project_id,
            onSelect: () => updateIssue.mutate({ project_id: p.id }),
          })),
        ]}
      />

      <RailField
        label="Estimativa"
        valueText={issue.estimate ? `${issue.estimate} pts` : "—"}
        options={[
          {
            key: NONE,
            label: "Sem estimativa",
            checked: !issue.estimate,
            onSelect: () => updateIssue.mutate({ estimate: undefined }),
          },
          ...ISSUE_ESTIMATE_OPTIONS.map((points) => ({
            key: String(points),
            label: `${points} pts`,
            checked: points === issue.estimate,
            onSelect: () => updateIssue.mutate({ estimate: points }),
          })),
        ]}
      />

      <RailField
        label="Vencimento"
        valueText={issue.due_date ? formatDate(issue.due_date) : "—"}
        options={[
          {
            key: NONE,
            label: "Sem vencimento",
            checked: !issue.due_date,
            onSelect: () => updateIssue.mutate({ due_date: undefined }),
          },
          {
            key: "tomorrow",
            label: "Amanhã",
            checked: issue.due_date === quickDueDate(1),
            onSelect: () => updateIssue.mutate({ due_date: quickDueDate(1) }),
          },
          {
            key: "1w",
            label: "Em uma semana",
            checked: issue.due_date === quickDueDate(7),
            onSelect: () => updateIssue.mutate({ due_date: quickDueDate(7) }),
          },
          {
            key: "2w",
            label: "Em duas semanas",
            checked: issue.due_date === quickDueDate(14),
            onSelect: () => updateIssue.mutate({ due_date: quickDueDate(14) }),
          },
        ]}
      />

      <div>
        <div className="mb-1.5 text-[10.5px] font-semibold tracking-wide text-t3 uppercase">
          Labels
        </div>
        <IssueLabelPicker workspaceId={workspaceId} issueId={issue.id} />
      </div>

      <div className="border-t pt-3.5 text-[11.5px] leading-relaxed text-t3">
        Criada em {formatDate(issue.created_at)}
        <br />
        Atualizada em {formatDate(issue.updated_at)}
      </div>
    </aside>
  );
}
