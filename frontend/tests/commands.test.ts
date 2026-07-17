import { describe, expect, it, vi } from "vitest";

import type { WorkspaceMembershipSummary } from "@/features/auth/types";
import {
  buildNavigationCommands,
  buildUtilityCommands,
  buildWorkspaceSwitchCommands,
} from "@/shared/components/command-palette/commands";

describe("buildNavigationCommands", () => {
  it("navigates to the workspace-scoped route for each static command", () => {
    const navigate = vi.fn();
    const commands = buildNavigationCommands(navigate, "acme");

    const issuesCommand = commands.find((command) => command.id === "nav:issues");
    expect(issuesCommand?.to).toBe("/w/acme/issues");

    issuesCommand?.perform();
    expect(navigate).toHaveBeenCalledWith("/w/acme/issues");
  });

  it("includes a command for every core workspace section", () => {
    const commands = buildNavigationCommands(vi.fn(), "acme");
    expect(commands.map((command) => command.id)).toEqual([
      "nav:issues",
      "nav:projects",
      "nav:labels",
      "nav:settings",
    ]);
  });
});

describe("buildWorkspaceSwitchCommands", () => {
  const workspaces: WorkspaceMembershipSummary[] = [
    { id: "1", name: "Acme", slug: "acme", role: "OWNER" },
    { id: "2", name: "Beta", slug: "beta", role: "MEMBER" },
  ];

  it("excludes the currently active workspace", () => {
    const commands = buildWorkspaceSwitchCommands(vi.fn(), workspaces, "acme");
    expect(commands).toHaveLength(1);
    expect(commands[0]?.label).toBe("Mudar para Beta");
  });

  it("navigates to the target workspace's issues page", () => {
    const navigate = vi.fn();
    const commands = buildWorkspaceSwitchCommands(navigate, workspaces, "acme");

    commands[0]?.perform();
    expect(navigate).toHaveBeenCalledWith("/w/beta/issues");
  });
});

describe("buildUtilityCommands", () => {
  it("wires theme commands to setTheme and the logout command to logout", () => {
    const setTheme = vi.fn();
    const logout = vi.fn();
    const commands = buildUtilityCommands({ setTheme, logout });

    commands.find((command) => command.id === "action:theme-dark")?.perform();
    expect(setTheme).toHaveBeenCalledWith("dark");

    commands.find((command) => command.id === "action:logout")?.perform();
    expect(logout).toHaveBeenCalledOnce();
  });
});
