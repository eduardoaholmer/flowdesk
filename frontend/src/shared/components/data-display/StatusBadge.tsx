import type { VariantProps } from "class-variance-authority";
import type { LucideIcon } from "lucide-react";

import { Badge, type badgeVariants } from "@/shared/components/ui/badge";

type BadgeVariant = NonNullable<VariantProps<typeof badgeVariants>["variant"]>;

interface StatusBadgeProps {
  label: string;
  variant?: BadgeVariant;
  icon?: LucideIcon;
}

/**
 * Badge de status/prioridade genérico sobre `ui/badge.tsx` — para a Sprint 9 usar em
 * novos contextos (ex.: dashboard, kanban). Não substitui `IssueStatusBadge`/
 * `ProjectStatusBadge`/`IssuePriorityBadge` (`features/issues|projects/components/`),
 * que continuam como estão — cada um já resolve seu próprio mapeamento
 * enum-de-domínio → label/variante e migrá-los é risco desnecessário para o ganho
 * (ver plano da Sprint 8.8/8.9).
 */
export function StatusBadge({ label, variant = "secondary", icon: Icon }: StatusBadgeProps) {
  return (
    <Badge variant={variant}>
      {Icon && <Icon />}
      {label}
    </Badge>
  );
}
