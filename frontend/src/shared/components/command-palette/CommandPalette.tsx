import { useQuery } from "@tanstack/react-query";
import { Clock, FolderKanban, ListTodo } from "lucide-react";
import { useTheme } from "next-themes";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { logout } from "@/features/auth/api";
import { listIssues } from "@/features/issues/api";
import { listProjects } from "@/features/projects/api";
import { useWorkspace } from "@/features/workspaces/useWorkspace";
import { Button } from "@/shared/components/ui/button";
import {
  Command,
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/shared/components/ui/command";
import { Spinner } from "@/shared/components/ui/spinner";
import { useCurrentUser } from "@/shared/hooks/useCurrentUser";
import { useDebouncedValue } from "@/shared/hooks/useDebouncedValue";
import { workspaceRoutes } from "@/shared/lib/routes";
import { useAuthStore } from "@/shared/stores/authStore";
import { useUiStore } from "@/shared/stores/uiStore";

import {
  buildNavigationCommands,
  buildUtilityCommands,
  buildWorkspaceSwitchCommands,
  type PaletteCommand,
} from "./commands";
import { useRecentCommands } from "./useRecentCommands";

const MIN_SEARCH_LENGTH = 2;
const SEARCH_RESULT_LIMIT = 5;

export function CommandPalette() {
  const navigate = useNavigate();
  const { setTheme } = useTheme();
  const clearAuth = useAuthStore((state) => state.clear);
  const isOpen = useUiStore((state) => state.isCommandPaletteOpen);
  const setOpen = useUiStore((state) => state.setCommandPaletteOpen);
  const { workspace } = useWorkspace();
  const { data: profile } = useCurrentUser();
  const { recent, addRecent } = useRecentCommands();
  const [query, setQuery] = useState("");
  const debouncedQuery = useDebouncedValue(query, 250);

  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setOpen(!useUiStore.getState().isCommandPaletteOpen);
      }
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [setOpen]);

  function handleOpenChange(next: boolean) {
    setOpen(next);
    if (!next) setQuery("");
  }

  async function handleLogout() {
    try {
      await logout();
    } finally {
      clearAuth();
      window.location.assign("/login");
    }
  }

  const searchTerm = debouncedQuery.trim();
  const searchEnabled = Boolean(workspace) && searchTerm.length >= MIN_SEARCH_LENGTH;

  const issueResults = useQuery({
    queryKey: ["command-palette", "issues", workspace?.id, searchTerm],
    queryFn: () =>
      listIssues(workspace!.id, {
        page: 1,
        per_page: SEARCH_RESULT_LIMIT,
        q: searchTerm,
        sort: "-updated_at",
      }),
    enabled: searchEnabled,
    staleTime: 10_000,
  });

  const projectResults = useQuery({
    queryKey: ["command-palette", "projects", workspace?.id, searchTerm],
    queryFn: () =>
      listProjects(workspace!.id, {
        page: 1,
        per_page: SEARCH_RESULT_LIMIT,
        search: searchTerm,
        sort: "-updated_at",
      }),
    enabled: searchEnabled,
    staleTime: 10_000,
  });

  const staticCommands: PaletteCommand[] = [
    ...(workspace ? buildNavigationCommands(navigate, workspace.slug) : []),
    ...(workspace
      ? buildWorkspaceSwitchCommands(navigate, profile?.workspaces ?? [], workspace.slug)
      : []),
    ...buildUtilityCommands({ setTheme, logout: handleLogout }),
  ];

  function matchesQuery(command: PaletteCommand) {
    if (!query.trim()) return true;
    const haystack = `${command.label} ${command.keywords?.join(" ") ?? ""}`.toLowerCase();
    return haystack.includes(query.trim().toLowerCase());
  }

  function runCommand(command: PaletteCommand) {
    command.perform();
    if (command.to) {
      addRecent({ id: command.id, label: command.label, to: command.to });
    }
    setOpen(false);
  }

  function openRecent(entry: { id: string; label: string; to: string }) {
    navigate(entry.to);
    addRecent(entry);
    setOpen(false);
  }

  const filteredStatic = staticCommands.filter(matchesQuery);
  const showRecent = !query.trim() && recent.length > 0;
  const hasAsyncResults =
    searchEnabled &&
    ((issueResults.data && issueResults.data.data.length > 0) ||
      (projectResults.data && projectResults.data.data.length > 0));
  const isSearching = searchEnabled && (issueResults.isFetching || projectResults.isFetching);
  const hasSearchError =
    searchEnabled && !isSearching && (issueResults.isError || projectResults.isError);
  const isEmpty =
    !showRecent &&
    !isSearching &&
    !hasSearchError &&
    filteredStatic.length === 0 &&
    !hasAsyncResults;

  function retrySearch() {
    if (issueResults.isError) issueResults.refetch();
    if (projectResults.isError) projectResults.refetch();
  }

  return (
    <CommandDialog
      open={isOpen}
      onOpenChange={handleOpenChange}
      title="Paleta de comandos"
      description="Navegue, busque issues/projetos ou execute uma ação rápida."
    >
      <Command shouldFilter={false}>
        <CommandInput
          placeholder="Digite um comando ou busque issues/projetos…"
          value={query}
          onValueChange={setQuery}
        />
        <CommandList>
          {isEmpty && <CommandEmpty>Nenhum resultado encontrado.</CommandEmpty>}

          {isSearching && (
            <div className="flex items-center justify-center gap-2 px-2 py-6 text-sm text-muted-foreground">
              <Spinner />
              Buscando…
            </div>
          )}

          {hasSearchError && (
            <div className="flex flex-col items-center gap-2 px-2 py-6 text-center text-sm">
              <p className="text-muted-foreground">Não foi possível buscar issues/projetos.</p>
              <Button variant="outline" size="sm" onClick={retrySearch}>
                Tentar novamente
              </Button>
            </div>
          )}

          {showRecent && (
            <CommandGroup heading="Recentes">
              {recent.map((entry) => (
                <CommandItem key={entry.id} value={entry.id} onSelect={() => openRecent(entry)}>
                  <Clock />
                  {entry.label}
                </CommandItem>
              ))}
            </CommandGroup>
          )}

          {filteredStatic.length > 0 && (
            <CommandGroup heading="Comandos">
              {filteredStatic.map((command) => (
                <CommandItem
                  key={command.id}
                  value={command.id}
                  onSelect={() => runCommand(command)}
                >
                  <command.icon />
                  {command.label}
                </CommandItem>
              ))}
            </CommandGroup>
          )}

          {searchEnabled && issueResults.data && issueResults.data.data.length > 0 && (
            <CommandGroup heading="Issues">
              {issueResults.data.data.map((issue) => {
                const to = workspaceRoutes.issueDetail(workspace!.slug, issue.id);
                return (
                  <CommandItem
                    key={issue.id}
                    value={`issue-${issue.id}`}
                    onSelect={() =>
                      openRecent({
                        id: `issue:${issue.id}`,
                        label: `${issue.identifier} · ${issue.title}`,
                        to,
                      })
                    }
                  >
                    <ListTodo />
                    <span className="truncate">
                      <span className="text-muted-foreground">{issue.identifier}</span>{" "}
                      {issue.title}
                    </span>
                  </CommandItem>
                );
              })}
            </CommandGroup>
          )}

          {searchEnabled && projectResults.data && projectResults.data.data.length > 0 && (
            <CommandGroup heading="Projetos">
              {projectResults.data.data.map((project) => {
                const to = workspaceRoutes.projectDetail(workspace!.slug, project.id);
                return (
                  <CommandItem
                    key={project.id}
                    value={`project-${project.id}`}
                    onSelect={() =>
                      openRecent({ id: `project:${project.id}`, label: project.name, to })
                    }
                  >
                    <FolderKanban />
                    {project.name}
                  </CommandItem>
                );
              })}
            </CommandGroup>
          )}
        </CommandList>
      </Command>
    </CommandDialog>
  );
}
