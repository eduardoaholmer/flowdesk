import { describe, expect, it } from "vitest";

import { invitationAcceptRoute, routePatterns, workspaceRoutes } from "@/shared/lib/routes";

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
