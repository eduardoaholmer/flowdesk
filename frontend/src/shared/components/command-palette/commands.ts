import {
  Building2,
  FolderKanban,
  ListTodo,
  LogOut,
  Moon,
  Settings,
  Sun,
  SunMoon,
  Tags,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import type { NavigateFunction } from "react-router-dom";

import type { WorkspaceMembershipSummary } from "@/features/auth/types";
import { workspaceRoutes } from "@/shared/lib/routes";

/**
 * Um comando estático não depende de resultado de rede — cobre navegação,
 * troca de workspace e ações utilitárias. Resultados de busca (issues/
 * projetos) são montados à parte em `CommandPalette.tsx`, já que dependem de
 * uma query assíncrona por termo digitado, não de uma lista fixa.
 *
 * Extensão futura: um novo grupo de comandos estáticos é uma nova função
 * `buildXCommands(...)` aqui + uma chamada em `CommandPalette.tsx` — nenhuma
 * outra peça do componente muda.
 */
export interface PaletteCommand {
  id: string;
  label: string;
  icon: LucideIcon;
  keywords?: string[];
  perform: () => void;
  /** Presente só em comandos de navegação — usado para registrar em "Recentes". */
  to?: string;
}

export function buildNavigationCommands(
  navigate: NavigateFunction,
  workspaceSlug: string,
): PaletteCommand[] {
  return [
    {
      id: "nav:issues",
      label: "Ir para Issues",
      icon: ListTodo,
      to: workspaceRoutes.issues(workspaceSlug),
      perform: () => navigate(workspaceRoutes.issues(workspaceSlug)),
    },
    {
      id: "nav:projects",
      label: "Ir para Projetos",
      icon: FolderKanban,
      to: workspaceRoutes.projects(workspaceSlug),
      perform: () => navigate(workspaceRoutes.projects(workspaceSlug)),
    },
    {
      id: "nav:labels",
      label: "Ir para Labels",
      icon: Tags,
      to: workspaceRoutes.labels(workspaceSlug),
      perform: () => navigate(workspaceRoutes.labels(workspaceSlug)),
    },
    {
      id: "nav:settings",
      label: "Ir para Configurações",
      icon: Settings,
      keywords: ["membros", "convites", "workspace"],
      to: workspaceRoutes.settings(workspaceSlug),
      perform: () => navigate(workspaceRoutes.settings(workspaceSlug)),
    },
  ];
}

export function buildWorkspaceSwitchCommands(
  navigate: NavigateFunction,
  workspaces: WorkspaceMembershipSummary[],
  currentSlug: string,
): PaletteCommand[] {
  return workspaces
    .filter((workspace) => workspace.slug !== currentSlug)
    .map((workspace) => ({
      id: `workspace:${workspace.id}`,
      label: `Mudar para ${workspace.name}`,
      icon: Building2,
      to: workspaceRoutes.issues(workspace.slug),
      perform: () => navigate(workspaceRoutes.issues(workspace.slug)),
    }));
}

export function buildUtilityCommands({
  setTheme,
  logout,
}: {
  setTheme: (theme: string) => void;
  logout: () => void;
}): PaletteCommand[] {
  return [
    { id: "action:theme-light", label: "Tema: Claro", icon: Sun, perform: () => setTheme("light") },
    { id: "action:theme-dark", label: "Tema: Escuro", icon: Moon, perform: () => setTheme("dark") },
    {
      id: "action:theme-system",
      label: "Tema: Sistema",
      icon: SunMoon,
      perform: () => setTheme("system"),
    },
    { id: "action:logout", label: "Sair da conta", icon: LogOut, perform: logout },
  ];
}
