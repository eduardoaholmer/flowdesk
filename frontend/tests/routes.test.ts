import { describe, expect, it } from "vitest";

import {
  invitationAcceptRoute,
  resolveLoginRedirect,
  routePatterns,
  workspaceRoutes,
} from "@/shared/lib/routes";

describe("workspaceRoutes.settings", () => {
  it("builds the workspace settings path from a slug", () => {
    expect(workspaceRoutes.settings("acme")).toBe("/w/acme/settings");
  });
});

describe("invitationAcceptRoute", () => {
  it("builds the invitation accept path from a token", () => {
    expect(invitationAcceptRoute("abc123")).toBe("/invitations/abc123/accept");
  });
});

describe("routePatterns", () => {
  it("declares matching patterns for settings and invitation accept", () => {
    expect(routePatterns.settings).toBe("/w/:workspaceSlug/settings");
    expect(routePatterns.invitationAccept).toBe("/invitations/:token/accept");
  });
});

describe("resolveLoginRedirect", () => {
  it("falls back to home when there is no from location", () => {
    expect(resolveLoginRedirect(null)).toBe("/");
    expect(resolveLoginRedirect(undefined)).toBe("/");
    expect(resolveLoginRedirect({})).toBe("/");
  });

  it("rebuilds the original path (including query string) from RequireAuth's from location", () => {
    const state = {
      from: { pathname: "/invitations/abc123/accept", search: "" },
    };

    expect(resolveLoginRedirect(state)).toBe("/invitations/abc123/accept");
  });

  it("preserves the query string of the original location", () => {
    const state = {
      from: { pathname: "/w/acme/issues", search: "?status=open" },
    };

    expect(resolveLoginRedirect(state)).toBe("/w/acme/issues?status=open");
  });
});
