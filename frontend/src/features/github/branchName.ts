const MAX_SLUG_LENGTH = 50;

/**
 * Nome de branch no formato que o vínculo de PRs reconhece (`fd-123-titulo-em-slug`,
 * mesma convenção do Linear): o identificador vem primeiro, então qualquer corte no
 * título nunca o perde.
 */
export function issueBranchName(identifier: string, title: string): string {
  const slug = title
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, MAX_SLUG_LENGTH)
    .replace(/-+$/, "");
  const prefix = identifier.toLowerCase();
  return slug ? `${prefix}-${slug}` : prefix;
}
