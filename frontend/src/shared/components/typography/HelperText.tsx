import type { ReactNode } from "react";

import { cn } from "@/shared/lib/utils";

interface HelperTextProps {
  children: ReactNode;
  error?: boolean;
  className?: string;
}

/**
 * Texto auxiliar leve para contextos **fora** de um formulário (ex.: legenda sob um
 * `StatCard`, nota sob um filtro). Dentro de um formulário real, use
 * `FieldDescription`/`FieldError` (`ui/field.tsx`) — já cobrem esse caso com o
 * contrato de acessibilidade correto (`role="alert"` em erro, associação via
 * `aria-describedby` do `Field`); este componente não duplica isso.
 */
export function HelperText({ children, error, className }: HelperTextProps) {
  return (
    <p
      role={error ? "alert" : undefined}
      className={cn("text-sm", error ? "text-destructive" : "text-muted-foreground", className)}
    >
      {children}
    </p>
  );
}
