import { ThemeToggle } from "@/shared/components/ThemeToggle";

/**
 * Placeholder — Sprint 1 (Fundação). Busca, notificações e avatar de usuário
 * chegam junto com as features que os alimentam (Sprint 2+), ver CLAUDE.md §1.6.
 */
export function Topbar() {
  return (
    <header className="flex h-14 items-center justify-between border-b px-4">
      <span className="text-sm font-medium text-muted-foreground">FlowDesk</span>
      <ThemeToggle />
    </header>
  );
}
