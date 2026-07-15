import type { ReactNode } from "react";

interface NotFoundStateProps {
  title?: string;
  description?: string;
  action?: ReactNode;
}

/**
 * Estado 404 genérico — extraído de `pages/NotFoundPage.tsx` (que agora só compõe
 * isto) para também servir casos inline (ex.: "esta issue não existe mais" dentro de
 * uma página que, no geral, existe).
 */
export function NotFoundState({
  title = "404",
  description = "Página não encontrada.",
  action,
}: NotFoundStateProps) {
  return (
    <div className="flex flex-col items-center justify-center gap-4 py-16 text-center">
      <h1 className="text-4xl font-semibold">{title}</h1>
      <p className="text-muted-foreground">{description}</p>
      {action}
    </div>
  );
}
