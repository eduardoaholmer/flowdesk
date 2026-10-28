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

export type GitHubPullRequestState = "OPEN" | "DRAFT" | "MERGED" | "CLOSED";

/** PR do GitHub que cita a issue (`FD-123`) na branch, no título ou no corpo. */
export interface GitHubPullRequestLink {
  id: string;
  repository_full_name: string;
  pr_number: number;
  pr_url: string;
  pr_title: string;
  pr_state: GitHubPullRequestState;
  author_login: string;
  head_branch: string;
  pr_updated_at: string;
}

export type GitHubAutomationEvent = "PR_DRAFT" | "PR_OPEN" | "PR_MERGED" | "PR_CLOSED";

/** Regra "PR nesta situação → issues vinculadas neste status"; `null` é sem ação. */
export interface GitHubStatusAutomation {
  event: GitHubAutomationEvent;
  target_state_id: string | null;
}
