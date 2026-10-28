import { expect, type Page, test } from "@playwright/test";

/**
 * Fluxo de conexão do GitHub App (Sprint 10.5, ADR-076) contra o backend real:
 * aba Integrações → "Conectar GitHub" → saída para github.com → volta pelo
 * `GET /integrations/github/setup` → página de retorno → aba Integrações.
 *
 * A instalação no github.com é simulada interceptando a navegação: o "GitHub"
 * devolve o navegador para o backend como o GitHub de verdade faria. A troca do
 * `code` por token (servidor → GitHub) não acontece aqui — fica coberta pelos
 * testes de contrato com o cliente do GitHub substituído. Os dois retornos usados
 * não chegam a essa troca:
 * - `setup_action=request` (instalação aguardando o dono da organização) passa
 *   pela validação real de `state` + cookie e para antes de chamar o GitHub;
 * - um `state` que este navegador não iniciou é recusado logo na entrada.
 *
 * Exige o backend com `GITHUB_APP_*`/`GITHUB_WEBHOOK_SECRET` preenchidos (valores
 * fictícios bastam); sem eles a aba mostra "Integração indisponível" e o teste é
 * pulado.
 */
const API_URL = process.env.E2E_API_URL ?? "http://localhost:8000/api/v1";

async function openIntegrationsTab(page: Page) {
  const suffix = `${Date.now()}-${Math.floor(Math.random() * 1000)}`;
  const email = `e2e-github-${suffix}@example.com`;
  const password = "Senha-Forte123!";

  await page.goto("/login");
  await page.getByRole("button", { name: "Criar conta" }).click();
  await page.getByLabel("Nome").fill("E2E GitHub");
  await page.getByLabel("E-mail").fill(email);
  await page.getByLabel("Senha", { exact: true }).fill(password);
  await page.locator("form").getByRole("button", { name: "Criar conta" }).click();

  await page.getByRole("link", { name: "Esqueci minha senha" }).waitFor();
  await page.getByLabel("E-mail").fill(email);
  await page.getByLabel("Senha", { exact: true }).fill(password);
  await page.locator("form").getByRole("button", { name: "Entrar" }).click();

  await page.getByLabel("Nome do workspace").fill(`E2E GitHub ${suffix}`);
  await page.getByRole("button", { name: "Criar workspace" }).click();

  await page.getByRole("link", { name: "Configurações" }).click();
  await page.getByRole("tab", { name: "Integrações" }).click();

  const unavailable = page.getByText("Integração indisponível");
  await expect(page.getByText("Nenhuma conta conectada").or(unavailable)).toBeVisible();
  test.skip(await unavailable.isVisible(), "backend sem GITHUB_APP_* configurado");
}

/** Faz o papel do github.com: quando o navegador chega à página de instalação,
 * devolve-o para o backend com os parâmetros que `returnParams` montar. */
async function simulateGitHubInstall(
  page: Page,
  returnParams: (state: string) => Record<string, string>,
) {
  let installUrl: URL | undefined;
  await page.route("https://github.com/apps/**", async (route) => {
    installUrl = new URL(route.request().url());
    const state = installUrl.searchParams.get("state") ?? "";
    const query = new URLSearchParams(returnParams(state));
    await route.fulfill({
      status: 302,
      headers: { location: `${API_URL}/integrations/github/setup?${query}` },
    });
  });
  await page.getByRole("button", { name: "Conectar GitHub" }).click();
  return () => installUrl;
}

// Um teste só, com um cadastro e um login: `/auth/register` e `/auth/login` têm
// limite de 5 por minuto por IP, e a suíte E2E inteira precisa caber nele.
test("conectar GitHub: volta à aba Integrações e recusa state de outro navegador", async ({
  page,
}) => {
  await openIntegrationsTab(page);

  // 1. Instalação aguardando aprovação do dono da organização: `state` e cookie
  //    válidos, o backend para antes de falar com o GitHub.
  const installUrl = await simulateGitHubInstall(page, (state) => ({
    state,
    setup_action: "request",
  }));

  await expect(page).toHaveURL(/\/w\/[^/]+\/settings\?tab=integrations$/);
  await expect(page.getByText(/aguarda aprovação de um dono da organização/)).toBeVisible();
  await expect(page.getByRole("tab", { name: "Integrações" })).toHaveAttribute(
    "aria-selected",
    "true",
  );
  expect(installUrl()?.pathname).toMatch(/^\/apps\/[^/]+\/installations\/new$/);
  expect(installUrl()?.searchParams.get("state")).toBeTruthy();

  // 2. O "GitHub" devolve um `state` que este navegador não iniciou.
  await page.unrouteAll();
  await simulateGitHubInstall(page, () => ({
    state: "state-de-outro-navegador",
    code: "qualquer",
    installation_id: "42",
    setup_action: "install",
  }));

  await expect(page.getByText(/expirou ou foi iniciada em outro navegador/)).toBeVisible();
  await expect(page).toHaveURL(/\/w\/[^/]+\/settings\?tab=integrations$/);
  await expect(page.getByText("Nenhuma conta conectada")).toBeVisible();
});
