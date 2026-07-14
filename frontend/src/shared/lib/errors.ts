import { isAxiosError } from "axios";

import type { ApiErrorBody } from "./apiTypes";

export function getApiErrorMessage(
  error: unknown,
  fallback = "Algo deu errado. Tente novamente.",
): string {
  if (isAxiosError<ApiErrorBody>(error) && error.response?.data?.error?.message) {
    return error.response.data.error.message;
  }
  return fallback;
}
