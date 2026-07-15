import { Link } from "react-router-dom";

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/shared/components/ui/table";
import { workspaceRoutes } from "@/shared/lib/routes";

import { ProjectRowActions } from "./ProjectRowActions";
import { ProjectStatusBadge } from "./ProjectStatusBadge";
import type { Project } from "../types";

export function ProjectsTable({
  workspaceId,
  workspaceSlug,
  projects,
}: {
  workspaceId: string;
  workspaceSlug: string;
  projects: Project[];
}) {
  return (
    <div className="rounded-xl border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Projeto</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Descrição</TableHead>
            <TableHead className="w-32 text-right">Ações</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {projects.map((project) => (
            <TableRow key={project.id}>
              <TableCell>
                <Link
                  to={workspaceRoutes.projectDetail(workspaceSlug, project.id)}
                  className="flex items-center gap-2 font-medium hover:underline"
                >
                  {project.color && (
                    <span
                      className="inline-block size-2.5 shrink-0 rounded-full"
                      style={{ backgroundColor: project.color }}
                    />
                  )}
                  {project.icon && <span aria-hidden>{project.icon}</span>}
                  {project.name}
                </Link>
              </TableCell>
              <TableCell>
                <ProjectStatusBadge status={project.status} />
              </TableCell>
              <TableCell className="max-w-xs truncate text-muted-foreground">
                {project.description || "—"}
              </TableCell>
              <TableCell>
                <div className="flex justify-end">
                  <ProjectRowActions workspaceId={workspaceId} project={project} />
                </div>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
