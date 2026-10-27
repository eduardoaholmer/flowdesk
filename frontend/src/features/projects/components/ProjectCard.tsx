import { Link } from "react-router-dom";

import { useWorkspaceMembers } from "@/features/workspaces/hooks";
import { Avatar, AvatarFallback } from "@/shared/components/ui/avatar";
import { Badge } from "@/shared/components/ui/badge";
import { formatDate } from "@/shared/lib/date";
import { workspaceRoutes } from "@/shared/lib/routes";
import { getInitials } from "@/shared/lib/string";

import { ProjectRowActions } from "./ProjectRowActions";
import type { Project } from "../types";

/** Sombra sutil do cartão, mesmo one-off já usado em `IssueBoardCard` (M7,
 * handoff `Projetos e Labels.dc.html` não define um token próprio para isso). */
const CARD_SHADOW = { boxShadow: "0 1px 2px rgba(20,19,15,.04)" };

const MAX_AVATARS = 4;

export function ProjectCard({
  workspaceId,
  workspaceSlug,
  project,
}: {
  workspaceId: string;
  workspaceSlug: string;
  project: Project;
}) {
  const { data: members } = useWorkspaceMembers(workspaceId);
  const memberById = new Map((members ?? []).map((member) => [member.user.id, member.user]));
  const avatarMembers = project.member_ids
    .slice(0, MAX_AVATARS)
    .map((id) => memberById.get(id))
    .filter((member): member is NonNullable<typeof member> => Boolean(member));
  const progressPct =
    project.issue_count > 0
      ? Math.round((project.done_issue_count / project.issue_count) * 100)
      : 0;

  return (
    <div
      className="flex flex-col gap-3 rounded-xl border border-border bg-panel px-4.5 py-4 hover:border-border2"
      style={CARD_SHADOW}
    >
      <div className="flex items-center gap-2">
        <span className="shrink-0 rounded-[5px] border border-border px-1.5 py-0.5 text-[10.5px] font-semibold tracking-wide text-t3 uppercase">
          {project.key}
        </span>
        <Link
          to={workspaceRoutes.projectDetail(workspaceSlug, project.id)}
          className="min-w-0 flex-1 truncate font-heading text-[15.5px] font-semibold hover:underline"
        >
          {project.name}
        </Link>
        {project.status === "ARCHIVED" && (
          <Badge variant="secondary" className="shrink-0 text-[10px] uppercase">
            Arquivado
          </Badge>
        )}
      </div>

      <p className="line-clamp-2 min-h-9.5 text-[12.5px] leading-relaxed text-t2">
        {project.description || "Sem descrição por enquanto."}
      </p>

      <div className="flex items-center gap-2.5">
        <span className="block h-1 flex-1 overflow-hidden rounded-full bg-sunken">
          <span className="block h-full bg-foreground" style={{ width: `${progressPct}%` }} />
        </span>
        <span className="shrink-0 text-[11.5px] text-t3">
          {project.done_issue_count}/{project.issue_count} concluídas
        </span>
      </div>

      <div className="flex items-center gap-1.5">
        <div className="flex -space-x-1.5">
          {avatarMembers.map((member) => (
            <Avatar key={member.id} className="size-5.5 border border-border2 bg-sunken">
              <AvatarFallback className="bg-transparent text-[8px] font-semibold text-t2">
                {getInitials(member.name)}
              </AvatarFallback>
            </Avatar>
          ))}
        </div>
        <div className="flex-1" />
        <span className="shrink-0 text-[11.5px] text-t3">
          {project.target_date ? formatDate(project.target_date) : "Sem data"}
        </span>
        <ProjectRowActions workspaceId={workspaceId} project={project} />
      </div>
    </div>
  );
}
