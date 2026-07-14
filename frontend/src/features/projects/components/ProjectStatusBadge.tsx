import { Badge } from "@/shared/components/ui/badge";

import type { ProjectStatus } from "../types";

export function ProjectStatusBadge({ status }: { status: ProjectStatus }) {
  if (status === "ARCHIVED") {
    return <Badge variant="secondary">Arquivado</Badge>;
  }
  return <Badge variant="outline">Ativo</Badge>;
}
