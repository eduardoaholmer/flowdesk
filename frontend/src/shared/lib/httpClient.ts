import axios from "axios";

/**
 * Cliente HTTP central (docs/05-frontend.md §2). Nenhuma feature deve instanciar
 * axios diretamente — todas consomem esta instância, que concentra base URL e,
 * a partir da Sprint 2, o interceptor de autenticação (injeção de access token,
 * retry transparente de refresh em 401 — ver docs/07-security.md).
 */
export const httpClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  withCredentials: true,
});
