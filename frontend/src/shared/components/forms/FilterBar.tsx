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
 * (busca + filtros à esquerda, ação de criação à direita) em `IssuesToolbar`/
 * `ProjectsToolbar`. Empilha em coluna abaixo de `sm` (busca+filtros, depois a ação,
 * cada um em linha própria) e vira linha única a partir de `sm` — mesmo idioma de
 * `ui/dialog.tsx::DialogFooter` (`flex-col` → `sm:flex-row`) para o mesmo problema:
 * um `flex-wrap` solto com a ação como irmã do grupo de filtros deixava a ação
 * espremida ao lado de um filtro em vez de ter posição previsível em telas estreitas
 * (achado da revisão visual da Sprint 13.4, ver ADR-025). Só o layout: cada feature
 * continua dona dos seus próprios filtros/estado, este componente não sabe nada de
 * domínio.
 */
export function FilterBar({ search, filters, actions, className }: FilterBarProps) {
  return (
    <div
      className={cn(
        "flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between",
        className,
      )}
    >
      <div className="flex flex-1 flex-wrap items-center gap-2">
        {search}
        {filters}
      </div>
      {actions}
    </div>
  );
}
