import { describe, expect, it } from "vitest";

import { issueBranchName } from "@/features/github/branchName";

describe("issueBranchName", () => {
  it("prefixes the lowercase identifier and slugifies the title", () => {
    expect(issueBranchName("FD-123", "Corrigir login no Safari")).toBe(
      "fd-123-corrigir-login-no-safari",
    );
  });

  it("drops accents and punctuation", () => {
    expect(issueBranchName("FD-7", "Ação: não salvar rascunho (é bug!)")).toBe(
      "fd-7-acao-nao-salvar-rascunho-e-bug",
    );
  });

  it("caps the slug without leaving a trailing dash or losing the identifier", () => {
    const branch = issueBranchName("FD-9", "palavra ".repeat(20));

    expect(branch.startsWith("fd-9-palavra-")).toBe(true);
    expect(branch.length).toBeLessThanOrEqual("fd-9-".length + 50);
    expect(branch.endsWith("-")).toBe(false);
  });

  it("falls back to the identifier when the title has nothing to slugify", () => {
    expect(issueBranchName("FD-4", "!!! 🚀")).toBe("fd-4");
  });
});
