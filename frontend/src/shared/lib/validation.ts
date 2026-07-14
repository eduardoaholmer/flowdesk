/**
 * Validação de schema/formulário usa Zod (docs/09-decision-log.md ADR-004) —
 * estas são checagens pontuais fora do fluxo de formulário (ex.: um filtro de
 * busca), não um substituto para schemas Zod.
 */

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export function isValidEmail(value: string): boolean {
  return EMAIL_PATTERN.test(value);
}

export function isNonEmptyString(value: string | null | undefined): value is string {
  return typeof value === "string" && value.trim().length > 0;
}
