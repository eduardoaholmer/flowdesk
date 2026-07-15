import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

import {
  Empty,
  EmptyContent,
  EmptyDescription,
  EmptyHeader,
  EmptyMedia,
  EmptyTitle,
} from "@/shared/components/ui/empty";
import { cn } from "@/shared/lib/utils";

interface EmptyStateProps {
  icon: LucideIcon;
  title: string;
  description: string;
  action?: ReactNode;
  className?: string;
}

/**
 * Generaliza o padrão hoje duplicado em `IssuesEmptyState`/`ProjectsEmptyState`
 * — features envolvem isto com sua própria cópia/ícone/ação, nunca reimplementam
 * a casca visual (docs/05-frontend.md §2: componente sem conhecimento de domínio).
 */
export function EmptyState({ icon: Icon, title, description, action, className }: EmptyStateProps) {
  return (
    <Empty className={cn("border py-16", className)}>
      <EmptyHeader>
        <EmptyMedia>
          <Icon className="size-8 text-muted-foreground" />
        </EmptyMedia>
        <EmptyTitle>{title}</EmptyTitle>
        <EmptyDescription>{description}</EmptyDescription>
      </EmptyHeader>
      {action && <EmptyContent>{action}</EmptyContent>}
    </Empty>
  );
}
