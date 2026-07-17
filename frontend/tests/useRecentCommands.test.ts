import { act, renderHook } from "@testing-library/react";
import { beforeEach, describe, expect, it } from "vitest";

import { useRecentCommands } from "@/shared/components/command-palette/useRecentCommands";

describe("useRecentCommands", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it("starts empty", () => {
    const { result } = renderHook(() => useRecentCommands());
    expect(result.current.recent).toEqual([]);
  });

  it("adds an entry to the front of the list", () => {
    const { result } = renderHook(() => useRecentCommands());

    act(() => {
      result.current.addRecent({ id: "nav:issues", label: "Ir para Issues", to: "/w/acme/issues" });
    });

    expect(result.current.recent).toEqual([
      { id: "nav:issues", label: "Ir para Issues", to: "/w/acme/issues" },
    ]);
  });

  it("moves a re-added entry back to the front instead of duplicating it", () => {
    const { result } = renderHook(() => useRecentCommands());

    act(() => {
      result.current.addRecent({ id: "a", label: "A", to: "/a" });
      result.current.addRecent({ id: "b", label: "B", to: "/b" });
      result.current.addRecent({ id: "a", label: "A", to: "/a" });
    });

    expect(result.current.recent.map((entry) => entry.id)).toEqual(["a", "b"]);
  });

  it("caps the list at 5 entries", () => {
    const { result } = renderHook(() => useRecentCommands());

    act(() => {
      for (let i = 0; i < 8; i += 1) {
        result.current.addRecent({ id: `cmd-${i}`, label: `Cmd ${i}`, to: `/${i}` });
      }
    });

    expect(result.current.recent).toHaveLength(5);
    expect(result.current.recent[0]?.id).toBe("cmd-7");
  });
});
