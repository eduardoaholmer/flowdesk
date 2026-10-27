import { create } from "zustand";

import type { AuthUser } from "@/features/auth/types";

/**
 * Access token vive só em memória (Zustand sem `persist`) — nunca em
 * `localStorage` (CLAUDE.md §11). Sobrevive a navegação entre páginas da SPA,
 * mas some em um reload; `AuthBootstrap` (`src/app/AuthBootstrap.tsx`) reobtém
 * um novo access token a partir do refresh token em cookie `HttpOnly` nesse caso.
 *
 * `bootstrapStatus` é uma máquina de estados explícita (não um único booleano de
 * loading) porque "não consegui confirmar a sessão" tem duas causas bem
 * diferentes que a UI precisa reagir de formas diferentes (docs/09-decision-log.md
 * ADR-062): `"ready"` cobre tanto sessão válida quanto "legitimamente sem sessão"
 * (segue para `/login` normalmente); `"error"` é reservado para quando a própria
 * tentativa de verificar a sessão falhou por motivo alheio à autenticação (rede,
 * timeout, backend fora do ar) — nesse caso a UI mostra um estado de erro com
 * "tentar novamente" em vez de silenciosamente tratar o usuário como deslogado.
 */
type BootstrapStatus = "initializing" | "ready" | "error";

interface AuthState {
  accessToken: string | null;
  user: AuthUser | null;
  bootstrapStatus: BootstrapStatus;
  setAuth: (accessToken: string, user: AuthUser) => void;
  setAccessToken: (accessToken: string) => void;
  clear: () => void;
  setBootstrapped: () => void;
  setBootstrapError: () => void;
  retryBootstrap: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  accessToken: null,
  user: null,
  bootstrapStatus: "initializing",
  setAuth: (accessToken, user) => set({ accessToken, user, bootstrapStatus: "ready" }),
  setAccessToken: (accessToken) => set({ accessToken }),
  clear: () => set({ accessToken: null, user: null }),
  setBootstrapped: () => set({ bootstrapStatus: "ready" }),
  setBootstrapError: () => set({ bootstrapStatus: "error" }),
  retryBootstrap: () => set({ bootstrapStatus: "initializing" }),
}));
