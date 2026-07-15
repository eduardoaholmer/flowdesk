import type { ReactNode } from "react";

import { cn } from "@/shared/lib/utils";

interface SectionHeaderProps {
  title: string;
  description?: string;
  actions?: ReactNode;
  className?: string;
}

/** Sibling menor de `PageHeader`, para uma seção dentro de uma página (não a página inteira). */
export function SectionHeader({ title, description, actions, className }: SectionHeaderProps) {
  return (
    <div className={cn("flex items-start justify-between gap-4", className)}>
      <div>
        <h2 className="text-sm font-medium">{title}</h2>
        {description && <p className="text-sm text-muted-foreground">{description}</p>}
      </div>
      {actions}
    </div>
  );
}
