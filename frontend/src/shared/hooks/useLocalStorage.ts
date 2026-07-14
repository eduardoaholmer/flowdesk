import { useCallback, useState } from "react";

/**
 * Nunca usar para dado de sessão/autenticação (o access token vive só em
 * memória por design — CLAUDE.md §11). Serve para preferências de UI puras
 * (ex.: densidade de tabela) que devem sobreviver a um reload.
 */
export function useLocalStorage<T>(key: string, initialValue: T) {
  const [storedValue, setStoredValue] = useState<T>(() => {
    try {
      const item = window.localStorage.getItem(key);
      return item ? (JSON.parse(item) as T) : initialValue;
    } catch {
      return initialValue;
    }
  });

  const setValue = useCallback(
    (value: T | ((previous: T) => T)) => {
      setStoredValue((previous) => {
        const next = value instanceof Function ? value(previous) : value;
        try {
          window.localStorage.setItem(key, JSON.stringify(next));
        } catch {
          // Storage indisponível (modo privado, quota excedida) — segue só em memória.
        }
        return next;
      });
    },
    [key],
  );

  return [storedValue, setValue] as const;
}
