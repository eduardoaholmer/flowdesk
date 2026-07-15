import { Bell, LogOut, Menu, Search } from "lucide-react";
import { Link, useLocation, useParams } from "react-router-dom";

import { logout } from "@/features/auth/api";
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
import {
  CommandDialog,
  CommandEmpty,
  CommandInput,
  CommandList,
} from "@/shared/components/ui/command";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/shared/components/ui/dropdown-menu";
import { Empty, EmptyDescription, EmptyMedia, EmptyTitle } from "@/shared/components/ui/empty";
import { Popover, PopoverContent, PopoverTrigger } from "@/shared/components/ui/popover";
import { useCurrentUser } from "@/shared/hooks/useCurrentUser";
import { useDisclosure } from "@/shared/hooks/useDisclosure";
import { workspaceRoutes } from "@/shared/lib/routes";
import { getInitials } from "@/shared/lib/string";
import { useAuthStore } from "@/shared/stores/authStore";
import { useUiStore } from "@/shared/stores/uiStore";

const SECTION_LABELS: Record<string, string> = {
  issues: "Issues",
  projects: "Projetos",
  labels: "Labels",
};

function useBreadcrumbItems(workspaceSlug: string, workspaceName: string) {
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
    items.push({ label: "Detalhe" });
  }

  return items;
}

function TopbarBreadcrumb() {
  const { workspaceSlug } = useParams<{ workspaceSlug: string }>();
  const { data: profile } = useCurrentUser();
  const workspace = profile?.workspaces.find((w) => w.slug === workspaceSlug);
  const items = useBreadcrumbItems(workspaceSlug ?? "", workspace?.name ?? "FlowDesk");

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

/** Sem integração — ponto de extensão para busca cross-workspace de uma sprint futura. */
function TopbarSearch() {
  const dialog = useDisclosure();

  return (
    <>
      <Button
        variant="outline"
        size="sm"
        className="hidden gap-2 text-muted-foreground sm:flex"
        onClick={dialog.open}
      >
        <Search className="size-4" />
        Buscar…
      </Button>
      <Button
        variant="ghost"
        size="icon"
        className="sm:hidden"
        aria-label="Buscar"
        onClick={dialog.open}
      >
        <Search className="size-4" />
      </Button>
      <CommandDialog
        open={dialog.isOpen}
        onOpenChange={dialog.close}
        title="Buscar"
        description="Busca"
      >
        <CommandInput placeholder="Buscar issues, projetos, labels…" />
        <CommandList>
          <CommandEmpty>Busca ainda não disponível nesta versão.</CommandEmpty>
        </CommandList>
      </CommandDialog>
    </>
  );
}

/** Sem integração — não existe feature de notificações ainda (docs/08-roadmap.md, Sprint 9). */
function TopbarNotifications() {
  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button variant="ghost" size="icon" aria-label="Notificações">
          <Bell className="size-4" />
        </Button>
      </PopoverTrigger>
      <PopoverContent align="end" className="w-80">
        <Empty className="border-none p-2 py-6">
          <EmptyMedia>
            <Bell className="size-6 text-muted-foreground" />
          </EmptyMedia>
          <EmptyTitle>Nenhuma notificação</EmptyTitle>
          <EmptyDescription>
            Você será avisado aqui sobre menções e mudanças de status.
          </EmptyDescription>
        </Empty>
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
