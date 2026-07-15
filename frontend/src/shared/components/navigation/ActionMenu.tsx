import type { LucideIcon } from "lucide-react";
import { MoreHorizontal } from "lucide-react";

import { Button } from "@/shared/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/shared/components/ui/dropdown-menu";

export interface ActionMenuItem {
  label: string;
  icon?: LucideIcon;
  onClick: () => void;
  destructive?: boolean;
  disabled?: boolean;
}

interface ActionMenuProps {
  items: ActionMenuItem[];
  /** Anunciado ao trigger — sempre obrigatório, o botão só tem um ícone. */
  triggerLabel: string;
}

/**
 * Menu de ações genérico sobre `ui/dropdown-menu.tsx` — para quando uma linha/card
 * tem ações demais para caberem como botões de ícone lado a lado (o padrão hoje usado
 * por `IssueRowActions`/`ProjectRowActions`/`LabelRowActions`, que continuam como
 * estão — ver plano da Sprint 8.8/8.9). Reservado para os casos futuros da Sprint 9
 * com 3+ ações por item.
 */
export function ActionMenu({ items, triggerLabel }: ActionMenuProps) {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon-sm" aria-label={triggerLabel}>
          <MoreHorizontal />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        {items.map((item) => (
          <DropdownMenuItem
            key={item.label}
            variant={item.destructive ? "destructive" : "default"}
            disabled={item.disabled}
            onClick={item.onClick}
          >
            {item.icon && <item.icon />}
            {item.label}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
