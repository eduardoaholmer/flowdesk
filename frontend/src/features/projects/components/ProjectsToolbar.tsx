import { Search } from "lucide-react";

import { FilterBar } from "@/shared/components/forms/FilterBar";
import { Input } from "@/shared/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/shared/components/ui/select";

import { CreateProjectDialog } from "./CreateProjectDialog";
import type { ProjectStatus } from "../types";

export function ProjectsToolbar({
  workspaceId,
  search,
  onSearchChange,
  status,
  onStatusChange,
}: {
  workspaceId: string;
  search: string;
  onSearchChange: (value: string) => void;
  status: ProjectStatus | "ALL";
  onStatusChange: (value: ProjectStatus | "ALL") => void;
}) {
  return (
    <FilterBar
      search={
        <div className="relative w-full max-w-xs">
          <Search className="pointer-events-none absolute top-1/2 left-2.5 size-3.5 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={search}
            onChange={(event) => onSearchChange(event.target.value)}
            placeholder="Buscar projetos…"
            className="pl-8"
          />
        </div>
      }
      filters={
        <Select
          value={status}
          onValueChange={(value) => onStatusChange(value as ProjectStatus | "ALL")}
        >
          <SelectTrigger className="w-36">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="ALL">Todos os status</SelectItem>
            <SelectItem value="ACTIVE">Ativos</SelectItem>
            <SelectItem value="ARCHIVED">Arquivados</SelectItem>
          </SelectContent>
        </Select>
      }
      actions={<CreateProjectDialog workspaceId={workspaceId} />}
    />
  );
}
