import type { ReactNode } from "react";

import { cn } from "@/shared/lib/utils";

interface PageHeaderProps {
  title: string;
  description?: string;
  /** Botões/ações alinhados à direita do título (ex.: "Criar issue"). */
  actions?: ReactNode;
  className?: string;
}

/**
 * Cabeçalho padrão de página (título + descrição + ações) — absorve o pedido
 * separado de "PageTitle": um título de página sempre vive junto de descrição/ação
 * no layout real deste projeto (ver `IssuesListPage`/`ProjectsListPage`/
 * `LabelsListPage` hoje, todos com o mesmo par `<h1>`+`<p>` repetido inline), então
 * um segundo componente só-título recriaria a duplicação que este componente existe
 * para eliminar.
 */
export function PageHeader({ title, description, actions, className }: PageHeaderProps) {
  return (
    <div className={cn("flex items-start justify-between gap-4", className)}>
      <div>
        <h1 className="font-heading text-lg font-semibold">{title}</h1>
        {description && <p className="text-sm text-muted-foreground">{description}</p>}
      </div>
      {actions}
    </div>
  );
}
