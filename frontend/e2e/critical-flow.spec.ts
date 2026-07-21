import { expect, test } from "@playwright/test";

/**
 * Primeiro fluxo E2E do projeto (`CLAUDE.md` §16, DoD original da Sprint 6 —
 * nunca cumprido até a Sprint 14.4/M4). Cobre o caminho feliz ponta a ponta
 * contra um backend real (não MSW — E2E existe para o que dá confiança de "o
 * produto funciona", não para isolar unidades): cadastro → login → criar
 * workspace → criar issue → mudar status.
 *
 * Senha atende `_validate_strong_password` (backend/src/features/auth/schemas.py):
 * ≥10 caracteres, minúscula, maiúscula, dígito e símbolo.
 */
test("cadastro → login → criar workspace → criar issue → mudar status", async ({ page }) => {
  const suffix = `${Date.now()}-${Math.floor(Math.random() * 1000)}`;
  const name = "E2E Test User";
  const email = `e2e-${suffix}@example.com`;
  const password = "Senha-Forte123!";
  const workspaceName = `E2E Workspace ${suffix}`;
  const issueTitle = `E2E Issue ${suffix}`;

  await page.goto("/login");

  await page.getByRole("button", { name: "Criar conta" }).click();
  await page.getByLabel("Nome").fill(name);
  await page.getByLabel("E-mail").fill(email);
  await page.getByLabel("Senha").fill(password);
  await page.locator("form").getByRole("button", { name: "Criar conta" }).click();

  await page.getByRole("link", { name: "Esqueci minha senha" }).waitFor();
  await page.getByLabel("E-mail").fill(email);
  await page.getByLabel("Senha").fill(password);
  await page.locator("form").getByRole("button", { name: "Entrar" }).click();

  await expect(page.getByRole("heading", { name: "Crie seu primeiro workspace" })).toBeVisible();
  await page.getByLabel("Nome do workspace").fill(workspaceName);
  await page.getByRole("button", { name: "Criar workspace" }).click();

  await page.getByRole("link", { name: "Issues" }).click();
  await expect(page).toHaveURL(/\/issues$/);

  await page.getByRole("button", { name: "Nova issue" }).first().click();
  await page.getByLabel("Título").fill(issueTitle);
  await page.locator("form").getByRole("button", { name: "Criar issue" }).click();

  const issueLink = page.getByRole("link", { name: issueTitle });
  await issueLink.waitFor();
  await issueLink.click();
  await expect(page).toHaveURL(/\/issues\/[^/]+$/);
  await expect(page.getByText("Backlog", { exact: true })).toBeVisible();

  await page.getByRole("button", { name: "Editar issue" }).click();
  const dialog = page.getByRole("dialog");
  await expect(dialog).toBeVisible();
  await dialog.getByRole("combobox").first().click();
  await page.getByRole("option", { name: "In Progress" }).click();
  await dialog.getByRole("button", { name: "Salvar alterações" }).click();

  await expect(page.getByText("In Progress", { exact: true })).toBeVisible();
});
