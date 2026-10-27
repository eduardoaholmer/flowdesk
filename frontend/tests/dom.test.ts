import { describe, expect, it } from "vitest";

import { isTypingTarget } from "@/shared/lib/dom";

describe("isTypingTarget", () => {
  it("treats form fields and contentEditable elements as typing targets", () => {
    expect(isTypingTarget(document.createElement("input"))).toBe(true);
    expect(isTypingTarget(document.createElement("textarea"))).toBe(true);
    expect(isTypingTarget(document.createElement("select"))).toBe(true);

    const editable = document.createElement("div");
    editable.contentEditable = "true";
    expect(isTypingTarget(editable)).toBe(true);
  });

  it("does not treat a plain element or null as a typing target", () => {
    expect(isTypingTarget(document.createElement("div"))).toBe(false);
    expect(isTypingTarget(null)).toBe(false);
  });
});
