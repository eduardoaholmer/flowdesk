import {
  ChevronsUpDown,
  FolderKanban,
  ListTodo,
  PanelLeftClose,
  PanelLeftOpen,
  Tags,
  type LucideIcon,
} from "lucide-react";
import { Link, NavLink, useParams } from "react-router-dom";

import { Avatar, AvatarFallback } from "@/shared/components/ui/avatar";
import { Button } from "@/shared/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/shared/components/ui/dropdown-menu";
import { Sheet, SheetContent, SheetTitle } from "@/shared/components/ui/sheet";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/shared/components/ui/tooltip";
import { useBreakpoint } from "@/shared/hooks/useBreakpoint";
import { useCurrentUser } from "@/shared/hooks/useCurrentUser";
import { workspaceRoutes } from "@/shared/lib/routes";
import { getInitials } from "@/shared/lib/string";
import { cn } from "@/shared/lib/utils";
import { useUiStore } from "@/shared/stores/uiStore";

interface NavItem {
  label: string;
  to: string;
  icon: LucideIcon;
}

interface NavGroup {
  label: string;
  items: NavItem[];
}

function getNavGroups(workspaceSlug: string): NavGroup[] {
  return [
    {
      label: "Workspace",
      items: [
        { label: "Issues", to: workspaceRoutes.issues(workspaceSlug), icon: ListTodo },
        { label: "Projetos", to: workspaceRoutes.projects(workspaceSlug), icon: FolderKanban },
        { label: "Labels", to: workspaceRoutes.labels(workspaceSlug), icon: Tags },
      ],
    },
  ];
}

function SidebarNav({ workspaceSlug, collapsed }: { workspaceSlug: string; collapsed: boolean }) {
  const linkClassName = ({ isActive }: { isActive: boolean }) =>
    cn(
      "flex items-center gap-2 rounded-lg px-2.5 py-1.5 text-sm font-medium transition-colors",
      collapsed && "justify-center px-0",
      isActive ? "bg-muted text-foreground" : "text-muted-foreground hover:bg-muted/50",
    );

  return (
    <nav className="flex flex-1 flex-col gap-4 overflow-y-auto">
      {getNavGroups(workspaceSlug).map((group) => (
        <div key={group.label} className="flex flex-col gap-1">
          {!collapsed && (
            <span className="px-2.5 text-xs font-medium text-muted-foreground">{group.label}</span>
          )}
          {group.items.map((item) => {
            const link = (
              <NavLink key={item.to} to={item.to} className={linkClassName}>
                <item.icon className="size-4 shrink-0" />
                {!collapsed && item.label}
              </NavLink>
            );

            if (!collapsed) {
              return link;
            }

            return (
              <Tooltip key={item.to}>
                <TooltipTrigger asChild>{link}</TooltipTrigger>
                <TooltipContent side="right">{item.label}</TooltipContent>
              </Tooltip>
            );
          })}
        </div>
      ))}
    </nav>
  );
}

function WorkspaceSwitcher({
  workspaceSlug,
  collapsed,
}: {
  workspaceSlug: string;
  collapsed: boolean;
}) {
  const { data: profile } = useCurrentUser();
  const activeWorkspace = profile?.workspaces.find((workspace) => workspace.slug === workspaceSlug);

  if (!profile) {
    return null;
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          className={cn(
            "h-auto justify-start gap-2 px-2 py-1.5",
            collapsed && "justify-center px-0",
          )}
        >
          <Avatar size="sm">
            <AvatarFallback>{getInitials(activeWorkspace?.name ?? "?")}</AvatarFallback>
          </Avatar>
          {!collapsed && (
            <>
              <span className="flex-1 truncate text-left text-sm font-medium">
                {activeWorkspace?.name ?? "Workspace"}
              </span>
              <ChevronsUpDown className="size-3.5 shrink-0 text-muted-foreground" />
            </>
          )}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start" className="w-56">
        <DropdownMenuLabel>Workspaces</DropdownMenuLabel>
        <DropdownMenuSeparator />
        {profile.workspaces.map((workspace) => (
          <DropdownMenuItem key={workspace.id} asChild>
            <Link to={workspaceRoutes.issues(workspace.slug)}>
              <span className="flex-1 truncate">{workspace.name}</span>
              {workspace.slug === workspaceSlug && (
                <span className="text-xs text-muted-foreground">Ativo</span>
              )}
            </Link>
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

function SidebarFooter({ collapsed }: { collapsed: boolean }) {
  const { data: profile } = useCurrentUser();

  if (!profile) {
    return null;
  }

  return (
    <div className={cn("flex items-center gap-2 border-t pt-3", collapsed && "justify-center")}>
      <Avatar size="sm">
        <AvatarFallback>{getInitials(profile.name)}</AvatarFallback>
      </Avatar>
      {!collapsed && (
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-medium">{profile.name}</p>
          <p className="truncate text-xs text-muted-foreground">{profile.email}</p>
        </div>
      )}
    </div>
  );
}

function SidebarBody({ workspaceSlug, collapsed }: { workspaceSlug: string; collapsed: boolean }) {
  const toggleSidebar = useUiStore((state) => state.toggleSidebar);

  return (
    <div className="flex h-full flex-col gap-4 p-3">
      <WorkspaceSwitcher workspaceSlug={workspaceSlug} collapsed={collapsed} />
      <SidebarNav workspaceSlug={workspaceSlug} collapsed={collapsed} />
      <SidebarFooter collapsed={collapsed} />
      <Button
        variant="ghost"
        size="icon-sm"
        className="hidden self-end md:flex"
        aria-label={collapsed ? "Expandir menu" : "Recolher menu"}
        onClick={toggleSidebar}
      >
        {collapsed ? <PanelLeftOpen className="size-4" /> : <PanelLeftClose className="size-4" />}
      </Button>
    </div>
  );
}

/**
 * Trigger do menu mobile vive no Topbar (posição convencional) — compartilha
 * `isMobileNavOpen` via `uiStore` para não acoplar os dois componentes de
 * layout entre si além do necessário.
 */
export function Sidebar() {
  const { workspaceSlug } = useParams<{ workspaceSlug: string }>();
  const isSidebarCollapsed = useUiStore((state) => state.isSidebarCollapsed);
  const isMobileNavOpen = useUiStore((state) => state.isMobileNavOpen);
  const setMobileNavOpen = useUiStore((state) => state.setMobileNavOpen);
  const isDesktop = useBreakpoint("md");

  if (!workspaceSlug) {
    return null;
  }

  if (!isDesktop) {
    return (
      <Sheet open={isMobileNavOpen} onOpenChange={setMobileNavOpen}>
        <SheetContent side="left" className="w-64 p-0">
          <SheetTitle className="sr-only">Navegação</SheetTitle>
          <SidebarBody workspaceSlug={workspaceSlug} collapsed={false} />
        </SheetContent>
      </Sheet>
    );
  }

  return (
    <aside
      className={cn(
        "hidden shrink-0 flex-col border-r md:flex",
        isSidebarCollapsed ? "w-16" : "w-60",
      )}
    >
      <SidebarBody workspaceSlug={workspaceSlug} collapsed={isSidebarCollapsed} />
    </aside>
  );
}
