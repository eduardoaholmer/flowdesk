import { AlertTriangle } from "lucide-react";

import { Button } from "@/shared/components/ui/button";

export function ErrorState({
  message = "Não foi possível carregar os dados.",
  onRetry,
}: {
  message?: string;
  onRetry?: () => void;
}) {
  return (
    <div className="flex flex-col items-center gap-3 rounded-xl border border-dashed py-16 text-center">
      <AlertTriangle className="size-8 text-destructive" />
      <p className="text-sm font-medium">{message}</p>
      {onRetry && (
        <Button variant="outline" size="sm" onClick={onRetry}>
          Tentar novamente
        </Button>
      )}
    </div>
  );
}
