import { Search } from "lucide-react";

import { useProjects } from "@/features/projects/hooks";
import { FilterBar } from "@/shared/components/forms/FilterBar";
import { Input } from "@/shared/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/shared/components/ui/select";
import { MAX_PICKER_PAGE_SIZE } from "@/shared/lib/constants";

import type { IssuePriority, IssueSort, IssueStatus } from "../types";

const STATUS_OPTIONS: { value: IssueStatus; label: string }[] = [
  { value: "BACKLOG", label: "Backlog" },
  { value: "TODO", label: "Todo" },
  { value: "IN_PROGRESS", label: "In Progress" },
  { value: "IN_REVIEW", label: "In Review" },
  { value: "DONE", label: "Done" },
  { value: "CANCELED", label: "Canceled" },
];

const PRIORITY_OPTIONS: { value: IssuePriority; label: string }[] = [
  { value: "NO_PRIORITY", label: "No priority" },
  { value: "LOW", label: "Low" },
  { value: "MEDIUM", label: "Medium" },
  { value: "HIGH", label: "High" },
  { value: "URGENT", label: "Urgent" },
];

const SORT_OPTIONS: { value: IssueSort; label: string }[] = [
  { value: "-created_at", label: "Criação (mais recentes)" },
  { value: "created_at", label: "Criação (mais antigas)" },
  { value: "-updated_at", label: "Atualização (mais recentes)" },
  { value: "-priority", label: "Prioridade (maior primeiro)" },
  { value: "due_date", label: "Vencimento (mais próximo)" },
  { value: "number", label: "Identificador" },
];

export function IssuesToolbar({
  workspaceId,
  search,
  onSearchChange,
  status,
  onStatusChange,
  priority,
  onPriorityChange,
  projectId,
  onProjectChange,
  sort,
  onSortChange,
}: {
  workspaceId: string;
  search: string;
  onSearchChange: (value: string) => void;
  status: IssueStatus | "ALL";
  onStatusChange: (value: IssueStatus | "ALL") => void;
  priority: IssuePriority | "ALL";
  onPriorityChange: (value: IssuePriority | "ALL") => void;
  projectId: string | "ALL";
  onProjectChange: (value: string | "ALL") => void;
  sort: IssueSort;
  onSortChange: (value: IssueSort) => void;
}) {
  const { data: projects } = useProjects(workspaceId, {
    page: 1,
    per_page: MAX_PICKER_PAGE_SIZE,
    sort: "-created_at",
  });

  return (
    <FilterBar
      search={
        <div className="relative w-full max-w-xs">
          <Search className="pointer-events-none absolute top-1/2 left-2.5 size-3.5 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={search}
            onChange={(event) => onSearchChange(event.target.value)}
            placeholder="Buscar por título, descrição ou FD-123…"
            className="pl-8"
          />
        </div>
      }
      filters={
        <>
          <Select
            value={status}
            onValueChange={(value) => onStatusChange(value as IssueStatus | "ALL")}
          >
            <SelectTrigger className="w-40">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="ALL">Todos os status</SelectItem>
              {STATUS_OPTIONS.map((option) => (
                <SelectItem key={option.value} value={option.value}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select
            value={priority}
            onValueChange={(value) => onPriorityChange(value as IssuePriority | "ALL")}
          >
            <SelectTrigger className="w-40">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="ALL">Toda prioridade</SelectItem>
              {PRIORITY_OPTIONS.map((option) => (
                <SelectItem key={option.value} value={option.value}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select value={projectId} onValueChange={onProjectChange}>
            <SelectTrigger className="w-40">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="ALL">Todo projeto</SelectItem>
              {projects?.data.map((project) => (
                <SelectItem key={project.id} value={project.id}>
                  {project.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select value={sort} onValueChange={(value) => onSortChange(value as IssueSort)}>
            <SelectTrigger className="w-52">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {SORT_OPTIONS.map((option) => (
                <SelectItem key={option.value} value={option.value}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </>
      }
    />
  );
}
