import { create } from "zustand";

import type { AuthUser } from "@/features/auth/types";

/**
 * Access token vive só em memória (Zustand sem `persist`) — nunca em
 * `localStorage` (CLAUDE.md §11). Sobrevive a navegação entre páginas da SPA,
 * mas some em um reload; `AuthBootstrap` (`src/app/AuthBootstrap.tsx`) reobtém
 * um novo access token a partir do refresh token em cookie `HttpOnly` nesse caso.
 */
interface AuthState {
  accessToken: string | null;
  user: AuthUser | null;
  isBootstrapping: boolean;
  setAuth: (accessToken: string, user: AuthUser) => void;
  setAccessToken: (accessToken: string) => void;
  clear: () => void;
  setBootstrapped: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  accessToken: null,
  user: null,
  isBootstrapping: true,
  setAuth: (accessToken, user) => set({ accessToken, user, isBootstrapping: false }),
  setAccessToken: (accessToken) => set({ accessToken }),
  clear: () => set({ accessToken: null, user: null }),
  setBootstrapped: () => set({ isBootstrapping: false }),
}));
