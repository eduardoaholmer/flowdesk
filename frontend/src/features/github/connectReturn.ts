/**
 * O backend devolve o navegador para `/integrations/github/callback` sem dizer de
 * qual workspace a conexão partiu (o `state` só existe no servidor). O slug fica
 * guardado nesta aba antes de ir ao GitHub, para a página de retorno voltar à aba
 * Integrações certa. `sessionStorage` pode estar bloqueado; sem ele, a página de
 * retorno só cai na tela inicial.
 */
const STORAGE_KEY = "flowdesk:github-connect-workspace";

export function rememberGitHubConnectWorkspace(workspaceSlug: string): void {
  try {
    window.sessionStorage.setItem(STORAGE_KEY, workspaceSlug);
  } catch {
    // Armazenamento indisponível: o retorno cai na tela inicial.
  }
}

export function takeGitHubConnectWorkspace(): string | null {
  try {
    const workspaceSlug = window.sessionStorage.getItem(STORAGE_KEY);
    window.sessionStorage.removeItem(STORAGE_KEY);
    return workspaceSlug;
  } catch {
    return null;
  }
}
