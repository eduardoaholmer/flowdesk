import axios, { type AxiosError, type InternalAxiosRequestConfig } from "axios";

import { useAuthStore } from "@/shared/stores/authStore";

/**
 * Cliente HTTP central (docs/05-frontend.md §2). Nenhuma feature deve instanciar
 * axios diretamente — todas consomem esta instância, que concentra base URL e o
 * interceptor de autenticação (injeção de access token, retry transparente de
 * refresh em 401 — ver docs/07-security.md).
 */
export const httpClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  withCredentials: true,
});

httpClient.interceptors.request.use((config) => {
  const accessToken = useAuthStore.getState().accessToken;
  if (accessToken) {
    config.headers.set("Authorization", `Bearer ${accessToken}`);
  }
  return config;
});

function readCookie(name: string): string | null {
  const match = document.cookie.match(new RegExp(`(?:^|; )${name}=([^;]*)`));
  return match?.[1] ? decodeURIComponent(match[1]) : null;
}

/**
 * `POST /auth/refresh` é protegido por double-submit CSRF (CLAUDE.md §11): o
 * refresh token trafega só no cookie `HttpOnly`, e o header `X-CSRF-Token`
 * precisa bater com o cookie `csrf_token` (não-HttpOnly, por isso legível aqui).
 */
export async function refreshAccessToken(): Promise<string> {
  const csrfToken = readCookie("csrf_token");
  const response = await axios.post<{ data: { access_token: string } }>(
    `${import.meta.env.VITE_API_URL}/auth/refresh`,
    {},
    {
      withCredentials: true,
      headers: csrfToken ? { "X-CSRF-Token": csrfToken } : {},
    },
  );
  const accessToken = response.data.data.access_token;
  useAuthStore.getState().setAccessToken(accessToken);
  return accessToken;
}

type RetryableConfig = InternalAxiosRequestConfig & { _retry?: boolean };

// Deduplica chamadas de refresh concorrentes: várias requisições podem cair em
// 401 ao mesmo tempo (ex.: página que dispara 3 queries em paralelo com token
// expirado) — sem isso, cada uma dispararia seu próprio `/auth/refresh`.
let refreshPromise: Promise<string> | null = null;

httpClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as RetryableConfig | undefined;
    const isAuthEndpoint = originalRequest?.url?.includes("/auth/");

    if (
      error.response?.status !== 401 ||
      !originalRequest ||
      originalRequest._retry ||
      isAuthEndpoint
    ) {
      return Promise.reject(error);
    }

    originalRequest._retry = true;
    try {
      refreshPromise ??= refreshAccessToken().finally(() => {
        refreshPromise = null;
      });
      const accessToken = await refreshPromise;
      originalRequest.headers.set("Authorization", `Bearer ${accessToken}`);
      return httpClient(originalRequest);
    } catch (refreshError) {
      useAuthStore.getState().clear();
      window.location.assign("/login");
      return Promise.reject(refreshError);
    }
  },
);
