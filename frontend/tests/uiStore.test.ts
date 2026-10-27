import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const STORAGE_KEY = "flowdesk:sidebar-collapsed";

describe("uiStore sidebar collapse persistence", () => {
  beforeEach(() => {
    window.localStorage.clear();
    vi.resetModules();
  });

  afterEach(() => {
    window.localStorage.clear();
  });

  it("persists the collapsed state to localStorage on toggle", async () => {
    const { useUiStore } = await import("@/shared/stores/uiStore");

    expect(useUiStore.getState().isSidebarCollapsed).toBe(false);
    useUiStore.getState().toggleSidebar();

    expect(useUiStore.getState().isSidebarCollapsed).toBe(true);
    expect(window.localStorage.getItem(STORAGE_KEY)).toBe("1");
  });

  it("initializes from a previously persisted value", async () => {
    window.localStorage.setItem(STORAGE_KEY, "1");
    const { useUiStore } = await import("@/shared/stores/uiStore");

    expect(useUiStore.getState().isSidebarCollapsed).toBe(true);
  });
});
