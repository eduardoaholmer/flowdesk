/**
 * Larguras máximas de contêiner já em uso — fonte de verdade única consumida por
 * `PageContainer` (largura da página) e `ContentContainer` (largura de leitura de um
 * bloco dentro dela). Ver `docs/09-decision-log.md` ADR-019 (Milestone 3) — antes
 * dessa integração, os dois componentes declaravam a mesma ideia com objetos locais
 * próprios, sem nenhuma página real usando nenhum dos dois.
 */
export const pageContainerWidths = {
  md: "max-w-3xl",
  lg: "max-w-5xl",
  xl: "max-w-7xl",
  full: "max-w-none",
} as const;

export const contentContainerWidths = {
  sm: "max-w-md",
  md: "max-w-2xl",
} as const;

export type PageContainerWidth = keyof typeof pageContainerWidths;
export type ContentContainerWidth = keyof typeof contentContainerWidths;
