import { ProjectCard } from "./ProjectCard";
import type { Project } from "../types";

export function ProjectsGrid({
  workspaceId,
  workspaceSlug,
  projects,
}: {
  workspaceId: string;
  workspaceSlug: string;
  projects: Project[];
}) {
  return (
    <div className="grid grid-cols-[repeat(auto-fill,minmax(280px,1fr))] gap-3.5">
      {projects.map((project) => (
        <ProjectCard
          key={project.id}
          workspaceId={workspaceId}
          workspaceSlug={workspaceSlug}
          project={project}
        />
      ))}
    </div>
  );
}
