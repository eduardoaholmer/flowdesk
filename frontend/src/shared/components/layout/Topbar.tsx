import { Bell, LogOut, Menu, Search } from "lucide-react";
import { Link, useLocation, useParams } from "react-router-dom";

import { logout } from "@/features/auth/api";
import { useIssue } from "@/features/issues/hooks";
import { NotificationItem } from "@/features/notifications/components/NotificationItem";
import {
  useMarkAllNotificationsRead,
  useMarkNotificationRead,
  useRecentNotifications,
  useUnreadNotificationsCount,
} from "@/features/notifications/hooks";
import type { Notification } from "@/features/notifications/types";
import { useProject } from "@/features/projects/hooks";
import { Logo } from "@/shared/components/brand/Logo";
import { ThemeToggle } from "@/shared/components/ThemeToggle";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/shared/components/ui/breadcrumb";
import { Avatar, AvatarFallback } from "@/shared/components/ui/avatar";
import { Button } from "@/shared/components/ui/button";
import { Kbd } from "@/shared/components/ui/kbd";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/shared/components/ui/dropdown-menu";
import { Empty, EmptyDescription, EmptyMedia, EmptyTitle } from "@/shared/components/ui/empty";
import { Popover, PopoverContent, PopoverTrigger } from "@/shared/components/ui/popover";
import { useCurrentUser } from "@/shared/hooks/useCurrentUser";
import { workspaceRoutes } from "@/shared/lib/routes";
import { getInitials } from "@/shared/lib/string";
import { useAuthStore } from "@/shared/stores/authStore";
import { useUiStore } from "@/shared/stores/uiStore";

const SECTION_LABELS: Record<string, string> = {
  issues: "Issues",
  board: "Board",
  projects: "Projetos",
  labels: "Labels",
  settings: "Configurações",
};

function useBreadcrumbItems(
  workspaceSlug: string,
  workspaceName: string,
  detailLabel: string | undefined,
) {
  const { pathname } = useLocation();
  const [, , section, detail] = pathname.split("/").filter(Boolean);

  const items: { label: string; to?: string }[] = [
    { label: workspaceName, to: workspaceRoutes.issues(workspaceSlug) },
  ];

  if (section) {
    // `section` é dinâmico (issues/projects/labels, lido da URL atual) — não dá para
    // usar um builder de `workspaceRoutes` sem reconstruir o mesmo `switch` que a URL
    // já resolveu; reconstrução direta aqui é o caso genuinamente dinâmico, não duplicação.
    items.push({
      label: SECTION_LABELS[section] ?? section,
      to: detail ? `/w/${workspaceSlug}/${section}` : undefined,
    });
  }

  if (detail) {
    items.push({ label: detailLabel ?? "…" });
  }

  return items;
}

function TopbarBreadcrumb() {
  const { workspaceSlug } = useParams<{ workspaceSlug: string }>();
  const { pathname } = useLocation();
  const { data: profile } = useCurrentUser();
  const workspace = profile?.workspaces.find((w) => w.slug === workspaceSlug);

  const [, , section, detail] = pathname.split("/").filter(Boolean);
  const isIssueDetail = section === "issues" && Boolean(detail);
  const isProjectDetail = section === "projects" && Boolean(detail);

  // Busca o identificador real da issue/projeto em detalhe — mesma query key da
  // página de detalhe (Sprint 6/7), então normalmente é um cache hit, sem round-trip
  // extra. `enabled` fica implícito: `issueId`/`projectId` vazio desliga a query.
  const { data: issue } = useIssue(workspace?.id ?? "", isIssueDetail ? (detail ?? "") : "");
  const { data: project } = useProject(workspace?.id ?? "", isProjectDetail ? (detail ?? "") : "");

  const detailLabel = isIssueDetail
    ? issue?.identifier
    : isProjectDetail
      ? project?.name
      : undefined;

  const items = useBreadcrumbItems(workspaceSlug ?? "", workspace?.name ?? "FlowDesk", detailLabel);

  if (!workspaceSlug) {
    return <Logo size="sm" />;
  }

  return (
    <Breadcrumb>
      <BreadcrumbList>
        {items.map((item, index) => (
          <span key={`${item.label}-${index}`} className="flex items-center gap-1.5">
            <BreadcrumbItem>
              {item.to ? (
                <BreadcrumbLink asChild>
                  <Link to={item.to}>{item.label}</Link>
                </BreadcrumbLink>
              ) : (
                <BreadcrumbPage>{item.label}</BreadcrumbPage>
              )}
            </BreadcrumbItem>
            {index < items.length - 1 && <BreadcrumbSeparator />}
          </span>
        ))}
      </BreadcrumbList>
    </Breadcrumb>
  );
}

/** Abre a paleta de comandos global (`shared/components/command-palette/`, montada
 * em `AppLayout`) — este botão é só um segundo ponto de entrada além de Cmd/Ctrl+K. */
function TopbarSearch() {
  const setCommandPaletteOpen = useUiStore((state) => state.setCommandPaletteOpen);

  return (
    <>
      <Button
        variant="outline"
        size="sm"
        className="hidden gap-2 text-muted-foreground sm:flex"
        onClick={() => setCommandPaletteOpen(true)}
      >
        <Search className="size-4" />
        Buscar…
        <Kbd className="ml-2">⌘K</Kbd>
      </Button>
      <Button
        variant="ghost"
        size="icon"
        className="sm:hidden"
        aria-label="Buscar"
        onClick={() => setCommandPaletteOpen(true)}
      >
        <Search className="size-4" />
      </Button>
    </>
  );
}

function TopbarNotifications() {
  const { data: profile } = useCurrentUser();
  const { data: notifications, isLoading } = useRecentNotifications();
  const { data: unreadCount } = useUnreadNotificationsCount();
  const markRead = useMarkNotificationRead();
  const markAllRead = useMarkAllNotificationsRead();

  function slugFor(workspaceId: string) {
    return profile?.workspaces.find((w) => w.id === workspaceId)?.slug ?? null;
  }

  function handleOpen(notification: Notification) {
    if (notification.read_at === null) {
      markRead.mutate(notification.id);
    }
  }

  const hasUnread = Boolean(unreadCount && unreadCount > 0);

  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button variant="ghost" size="icon" className="relative" aria-label="Notificações">
          <Bell className="size-4" />
          {hasUnread && (
            <span className="absolute right-1.5 top-1.5 size-2 rounded-full bg-primary" />
          )}
        </Button>
      </PopoverTrigger>
      <PopoverContent align="end" className="w-80 p-2">
        <div className="flex items-center justify-between px-1 pb-1">
          <span className="text-sm font-medium">Notificações</span>
          {hasUnread && (
            <Button
              variant="ghost"
              size="sm"
              className="h-auto p-1 text-xs"
              onClick={() => markAllRead.mutate()}
            >
              Marcar todas como lidas
            </Button>
          )}
        </div>
        {isLoading ? (
          <div className="flex flex-col gap-2 p-2">
            <div className="h-10 animate-pulse rounded-md bg-muted" />
            <div className="h-10 animate-pulse rounded-md bg-muted" />
          </div>
        ) : notifications && notifications.data.length > 0 ? (
          <div className="flex max-h-80 flex-col gap-0.5 overflow-y-auto">
            {notifications.data.map((notification) => (
              <NotificationItem
                key={notification.id}
                notification={notification}
                workspaceSlug={slugFor(notification.workspace_id)}
                onOpen={handleOpen}
              />
            ))}
          </div>
        ) : (
          <Empty className="border-none p-2 py-6">
            <EmptyMedia>
              <Bell className="size-6 text-muted-foreground" />
            </EmptyMedia>
            <EmptyTitle>Nenhuma notificação</EmptyTitle>
            <EmptyDescription>
              Você será avisado aqui sobre menções e mudanças de status.
            </EmptyDescription>
          </Empty>
        )}
      </PopoverContent>
    </Popover>
  );
}

function TopbarUserMenu() {
  const { data: profile } = useCurrentUser();
  const clearAuth = useAuthStore((state) => state.clear);

  async function handleLogout() {
    try {
      await logout();
    } finally {
      clearAuth();
      window.location.assign("/login");
    }
  }

  if (!profile) {
    return null;
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon" className="rounded-full">
          <Avatar size="sm">
            <AvatarFallback>{getInitials(profile.name)}</AvatarFallback>
          </Avatar>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuItem disabled className="text-xs text-muted-foreground">
          {profile.email}
        </DropdownMenuItem>
        <DropdownMenuItem onSelect={handleLogout}>
          <LogOut className="size-4" />
          Sair
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

export function Topbar() {
  const { workspaceSlug } = useParams<{ workspaceSlug: string }>();
  const setMobileNavOpen = useUiStore((state) => state.setMobileNavOpen);

  return (
    <header className="flex h-14 items-center justify-between gap-2 border-b px-4">
      <div className="flex min-w-0 items-center gap-2">
        {workspaceSlug && (
          <Button
            variant="ghost"
            size="icon"
            className="shrink-0 md:hidden"
            aria-label="Abrir menu"
            onClick={() => setMobileNavOpen(true)}
          >
            <Menu className="size-5" />
          </Button>
        )}
        <TopbarBreadcrumb />
      </div>
      <div className="flex items-center gap-2">
        <TopbarSearch />
        <TopbarNotifications />
        <ThemeToggle />
        <TopbarUserMenu />
      </div>
    </header>
  );
}
