import axios, { type AxiosError, type InternalAxiosRequestConfig } from "axios";

import { useAuthStore } from "@/shared/stores/authStore";

/**
 * Cliente HTTP central (docs/05-frontend.md §2). Nenhuma feature deve instanciar
 * axios diretamente — todas consomem esta instância, que concentra base URL e o
 * interceptor de autenticação (injeção de access token, retry transparente de
 * refresh em 401 — ver docs/07-security.md).
 *
 * `timeout` evita que uma chamada trave indefinidamente sem erro nem retorno —
 * sem isso, uma falha de rede/backend fora do padrão (não um 4xx/5xx normal, mas
 * uma conexão que nunca fecha) deixava qualquer tela dependente presa em loading
 * para sempre, sem chance de mostrar erro (docs/09-decision-log.md ADR-062).
 */
const DEFAULT_TIMEOUT_MS = 15_000;

export const httpClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  withCredentials: true,
  timeout: DEFAULT_TIMEOUT_MS,
});

/**
 * O backend de produção (Render free tier) "dorme" após ~15 min de inatividade e
 * pode levar até ~50s para acordar na primeira requisição seguinte (`DEPLOY.md`)
 * — exatamente a chamada de bootstrap (`AuthBootstrap`) mais provável de acontecer
 * depois de um período assim. Um timeout curto (`DEFAULT_TIMEOUT_MS`) trataria um
 * cold start normal como falha; esta chamada específica tolera mais tempo.
 */
const REFRESH_TIMEOUT_MS = 60_000;

/**
 * Distingue "o servidor respondeu dizendo que não há sessão válida" (401/422 — o
 * usuário legitimamente não está autenticado) de "a chamada falhou por outro
 * motivo" (timeout, rede fora do ar, 5xx) — as duas nunca deveriam ter o mesmo
 * tratamento: só a primeira significa "vá para a tela de login" (ADR-062).
 */
export function isAuthRejection(error: unknown): boolean {
  return axios.isAxiosError(error) && error.response !== undefined && error.response.status < 500;
}

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
      timeout: REFRESH_TIMEOUT_MS,
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
      // Só um 401/422 do próprio `/auth/refresh` significa "esta sessão não é mais
      // válida" — um timeout ou uma falha de servidor (Render acordando de um cold
      // start, Redis/DB fora do ar) não prova isso, e forçar logout+redirect nesse
      // caso derruba uma sessão válida por uma instabilidade passageira (ADR-062).
      // A requisição original apenas falha; quem chamou decide como reagir/repetir.
      if (isAuthRejection(refreshError)) {
        useAuthStore.getState().clear();
        window.location.assign("/login");
      }
      return Promise.reject(refreshError);
    }
  },
);
