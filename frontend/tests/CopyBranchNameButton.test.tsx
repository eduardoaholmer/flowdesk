import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { CopyBranchNameButton } from "@/features/github/components/CopyBranchNameButton";

describe("CopyBranchNameButton", () => {
  it("copies the branch name that links pull requests to the issue", async () => {
    // `userEvent.setup()` instala um clipboard próprio no `navigator` do jsdom.
    const user = userEvent.setup();
    render(<CopyBranchNameButton identifier="FD-12" title="Exportar relatório em CSV" />);

    await user.click(screen.getByRole("button", { name: "Copiar nome da branch" }));

    expect(await navigator.clipboard.readText()).toBe("fd-12-exportar-relatorio-em-csv");
  });
});
