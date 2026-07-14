const LOCALE = "pt-BR";

export function formatDate(value: string | Date): string {
  const date = value instanceof Date ? value : new Date(value);
  return date.toLocaleDateString(LOCALE);
}

export function formatDateTime(value: string | Date): string {
  const date = value instanceof Date ? value : new Date(value);
  return date.toLocaleString(LOCALE);
}
