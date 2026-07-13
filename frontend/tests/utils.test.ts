import { describe, expect, it } from "vitest";

import { cn } from "@/shared/lib/utils";

describe("cn", () => {
  it("merges class names and resolves Tailwind conflicts", () => {
    expect(cn("px-2 py-1", "px-4")).toBe("py-1 px-4");
  });

  it("drops falsy values", () => {
    const hidden: string | undefined = undefined;
    expect(cn("text-sm", hidden, "font-medium")).toBe("text-sm font-medium");
  });
});
