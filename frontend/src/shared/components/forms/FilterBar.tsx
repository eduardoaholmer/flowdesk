import type { ReactNode } from "react";

import { cn } from "@/shared/lib/utils";

interface FilterBarProps {
  /** Tipicamente um `SearchInput`. */
  search?: ReactNode;
  /** Selects/toggles de filtro — renderizados lado a lado, quebram linha em telas estreitas. */
  filters?: ReactNode;
  /** Ação alinhada à direita (ex.: "Criar issue"). */
  actions?: ReactNode;
  className?: string;
}

/**
 * Casca responsiva de toolbar de listagem — generaliza o layout hoje repetido
 * (busca + filtros à esquerda, ação de criação à direita, `flex-wrap` em mobile) em
 * `IssuesToolbar`/`ProjectsToolbar`. Só o layout: cada feature continua dona dos
 * seus próprios filtros/estado, este componente não sabe nada de domínio.
 */
export function FilterBar({ search, filters, actions, className }: FilterBarProps) {
  return (
    <div className={cn("flex flex-wrap items-center justify-between gap-3", className)}>
      <div className="flex flex-1 flex-wrap items-center gap-2">
        {search}
        {filters}
      </div>
      {actions}
    </div>
  );
}
