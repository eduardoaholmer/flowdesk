import { FolderKanban } from "lucide-react";
import { NavLink, useParams } from "react-router-dom";

import { cn } from "@/shared/lib/utils";

export function Sidebar() {
  const { workspaceSlug } = useParams<{ workspaceSlug: string }>();

  if (!workspaceSlug) {
    return null;
  }

  return (
    <aside className="hidden w-60 shrink-0 flex-col gap-1 border-r p-3 md:flex">
      <NavLink
        to={`/w/${workspaceSlug}/projects`}
        className={({ isActive }) =>
          cn(
            "flex items-center gap-2 rounded-lg px-2.5 py-1.5 text-sm font-medium transition-colors",
            isActive ? "bg-muted text-foreground" : "text-muted-foreground hover:bg-muted/50",
          )
        }
      >
        <FolderKanban className="size-4" />
        Projetos
      </NavLink>
    </aside>
  );
}
