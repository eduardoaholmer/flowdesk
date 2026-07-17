import { httpClient } from "@/shared/lib/httpClient";
import type { DataEnvelope } from "@/shared/lib/apiTypes";

import type { AuthUser } from "./types";

export interface LoginPayload {
  email: string;
  password: string;
}

export interface RegisterPayload {
  name: string;
  email: string;
  password: string;
}

interface TokenResponseBody {
  access_token: string;
  user: AuthUser;
}

export async function login(payload: LoginPayload): Promise<TokenResponseBody> {
  const { data } = await httpClient.post<DataEnvelope<TokenResponseBody>>("/auth/login", payload);
  return data.data;
}

export async function register(payload: RegisterPayload): Promise<AuthUser> {
  const { data } = await httpClient.post<DataEnvelope<AuthUser>>("/auth/register", payload);
  return data.data;
}

export async function logout(): Promise<void> {
  await httpClient.post("/auth/logout");
}

export async function requestPasswordReset(email: string): Promise<void> {
  await httpClient.post("/auth/password-reset/request", { email });
}

export async function confirmPasswordReset(payload: {
  token: string;
  new_password: string;
}): Promise<void> {
  await httpClient.post("/auth/password-reset/confirm", payload);
}
