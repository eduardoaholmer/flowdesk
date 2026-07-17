import type { ReactNode } from "react";

import {
  contentContainerWidths,
  type ContentContainerWidth,
} from "@/shared/theme/tokens/containers";
import { cn } from "@/shared/lib/utils";

interface ContentContainerProps {
  children: ReactNode;
  /** Largura de leitura — `sm` para formulário/diálogo, `md` (padrão) para conteúdo de detalhe. */
  size?: ContentContainerWidth;
  className?: string;
}

/**
 * Wrapper de conteúdo mais estreito que `PageContainer` — para o corpo de um
 * formulário ou de uma página de detalhe, não para a página inteira (que já tem seu
 * próprio padding via `PageContainer`). As duas existem porque resolvem problemas
 * diferentes: `PageContainer` é o padding/largura da página; este é a largura de
 * leitura de um bloco de conteúdo dentro dela.
 */
export function ContentContainer({ children, size = "md", className }: ContentContainerProps) {
  return (
    <div className={cn("mx-auto w-full", contentContainerWidths[size], className)}>{children}</div>
  );
}
