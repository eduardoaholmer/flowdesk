const LOCALE = "pt-BR";

export function formatNumber(value: number): string {
  return value.toLocaleString(LOCALE);
}

export function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max);
}
