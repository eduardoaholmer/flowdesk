import { LogOut } from "lucide-react";
import { useParams } from "react-router-dom";

import { logout } from "@/features/auth/api";
import { ThemeToggle } from "@/shared/components/ThemeToggle";
import { Avatar, AvatarFallback } from "@/shared/components/ui/avatar";
import { Button } from "@/shared/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/shared/components/ui/dropdown-menu";
import { useCurrentUser } from "@/shared/hooks/useCurrentUser";
import { useAuthStore } from "@/shared/stores/authStore";

function initials(name: string): string {
  return name
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join("");
}

export function Topbar() {
  const { workspaceSlug } = useParams<{ workspaceSlug: string }>();
  const { data: profile } = useCurrentUser();
  const clearAuth = useAuthStore((state) => state.clear);

  const workspace = profile?.workspaces.find((w) => w.slug === workspaceSlug);

  async function handleLogout() {
    try {
      await logout();
    } finally {
      clearAuth();
      window.location.assign("/login");
    }
  }

  return (
    <header className="flex h-14 items-center justify-between border-b px-4">
      <span className="text-sm font-medium text-muted-foreground">
        FlowDesk{workspace ? ` · ${workspace.name}` : ""}
      </span>
      <div className="flex items-center gap-2">
        <ThemeToggle />
        {profile && (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" className="rounded-full">
                <Avatar size="sm">
                  <AvatarFallback>{initials(profile.name)}</AvatarFallback>
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
        )}
      </div>
    </header>
  );
}
