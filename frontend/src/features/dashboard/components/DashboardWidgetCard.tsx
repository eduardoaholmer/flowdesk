import type { ReactNode } from "react";

/**
 * Casca de widget do Início — painel/cabeçalho uppercase reaproveitados pelos
 * três widgets (Minhas issues, Projetos ativos, Atividade recente), conforme o
 * handoff de redesign (M7, Sprint 18.5). Substitui o `Card` shadcn genérico só
 * aqui: mesma decisão de estilização própria já tomada por `IssueBoardCard`/
 * `IssueDetailRail` (M7, Sprints 18.2/18.3) para consumir os tokens `--panel`/
 * `--sunken`/`--t3` do handoff em vez do tema shadcn padrão.
 */
export function DashboardWidgetCard({
  title,
  action,
  children,
}: {
  title: string;
  action?: ReactNode;
  children: ReactNode;
}) {
  return (
    <section className="overflow-hidden rounded-xl border border-border bg-panel">
      <div className="flex items-center justify-between gap-2 border-b border-border px-4 py-3">
        <span className="text-[11px] font-semibold tracking-wide text-t3 uppercase">{title}</span>
        {action}
      </div>
      {children}
    </section>
  );
}
