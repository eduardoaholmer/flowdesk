import type { ReactNode } from "react";

import { pageContainerWidths, type PageContainerWidth } from "@/shared/theme/tokens/containers";
import { cn } from "@/shared/lib/utils";

interface PageContainerProps {
  children: ReactNode;
  /** Largura máxima do conteúdo — `xl` (padrão) para listas/tabelas, `md`/`lg` para conteúdo de leitura mais estreito. */
  maxWidth?: PageContainerWidth;
  className?: string;
}

/**
 * Casca de página de nível superior: centraliza e aplica padding responsivo
 * consistente. Único ponto de "largura máxima de página" do projeto — uma página
 * nova nunca declara seu próprio `max-w-*`/`px-*` solto (absorve o pedido de um
 * "ResponsiveContainer" separado: a responsividade é o `maxWidth` variável, não um
 * segundo componente).
 */
export function PageContainer({ children, maxWidth = "xl", className }: PageContainerProps) {
  return (
    <div
      className={cn(
        "mx-auto w-full px-4 py-6 sm:px-6 lg:px-8",
        pageContainerWidths[maxWidth],
        className,
      )}
    >
      {children}
    </div>
  );
}
