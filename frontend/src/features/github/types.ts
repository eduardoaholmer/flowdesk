export interface GitHubInstallation {
  id: string;
  installation_id: number;
  account_login: string;
  /** Valor cru do GitHub — hoje `"User"` ou `"Organization"`. */
  account_type: string;
  connected_by_id: string;
  suspended_at: string | null;
  created_at: string;
}

export interface GitHubIntegration {
  /** `false` quando o GitHub App não está configurado neste servidor. */
  configured: boolean;
  installations: GitHubInstallation[];
}

export interface GitHubConnectResult {
  install_url: string;
}
