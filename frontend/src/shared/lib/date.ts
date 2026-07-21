const LOCALE = "pt-BR";

export function formatDate(value: string | Date): string {
  const date = value instanceof Date ? value : new Date(value);
  return date.toLocaleDateString(LOCALE);
}

export function formatDateTime(value: string | Date): string {
  const date = value instanceof Date ? value : new Date(value);
  return date.toLocaleString(LOCALE);
}

/** "terça-feira, 21 de julho" — usado pelo cabeçalho do Início (M7, Sprint 18.5). */
export function formatLongDate(value: string | Date = new Date()): string {
  const date = value instanceof Date ? value : new Date(value);
  const text = date.toLocaleDateString(LOCALE, { weekday: "long", day: "numeric", month: "long" });
  return text.charAt(0).toUpperCase() + text.slice(1);
}

/** Saudação por horário do dia — mesma lógica do handoff de redesign (M7, `data.js::saudacao`). */
export function getGreeting(now: Date = new Date()): string {
  const hour = now.getHours();
  if (hour < 12) return "Bom dia";
  if (hour < 18) return "Boa tarde";
  return "Boa noite";
}

/**
 * Tempo relativo compacto ("agora", "5 min", "3 h", "2 d") com fallback para
 * `formatDate` além de uma semana — mesma escala do handoff de redesign (M7,
 * `data.js::timeAgo`), novo requisito da Sprint 18.4 ("tempo relativo" na
 * listagem de issues e no feed de atividade do Início).
 */
export function formatRelativeTime(value: string | Date): string {
  const date = value instanceof Date ? value : new Date(value);
  const seconds = (Date.now() - date.getTime()) / 1000;
  if (seconds < 60) return "agora";
  if (seconds < 3600) return `${Math.floor(seconds / 60)} min`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)} h`;
  if (seconds < 86400 * 7) return `${Math.floor(seconds / 86400)} d`;
  return formatDate(date);
}
