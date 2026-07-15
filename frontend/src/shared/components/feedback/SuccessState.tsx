import { CheckCircle2 } from "lucide-react";
import type { ReactNode } from "react";

interface SuccessStateProps {
  title?: string;
  description?: string;
  action?: ReactNode;
}

/**
 * Estado de sucesso em tela cheia/bloco (ex.: "convite aceito", "importação concluída")
 * — não substitui o toast (`sonner`, via `AppProviders`) usado para feedback pontual
 * de uma ação; este é para quando o sucesso É o conteúdo da tela.
 */
export function SuccessState({ title = "Tudo certo!", description, action }: SuccessStateProps) {
  return (
    <div className="flex flex-col items-center gap-3 py-16 text-center">
      <CheckCircle2 className="size-8 text-primary" />
      <p className="text-sm font-medium">{title}</p>
      {description && <p className="text-sm text-muted-foreground">{description}</p>}
      {action}
    </div>
  );
}
