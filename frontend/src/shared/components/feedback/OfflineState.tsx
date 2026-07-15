import { WifiOff } from "lucide-react";

import { Button } from "@/shared/components/ui/button";

interface OfflineStateProps {
  onRetry?: () => void;
}

/**
 * Estado "sem conexão" — presentacional apenas. Detectar o estado de rede real
 * (`navigator.onLine`/evento `offline`) e decidir quando mostrar isto é
 * responsabilidade de quem consome (Sprint 9), não deste componente.
 */
export function OfflineState({ onRetry }: OfflineStateProps) {
  return (
    <div className="flex flex-col items-center gap-3 rounded-xl border border-dashed py-16 text-center">
      <WifiOff className="size-8 text-muted-foreground" />
      <p className="text-sm font-medium">Sem conexão com a internet.</p>
      <p className="text-sm text-muted-foreground">Verifique sua rede e tente novamente.</p>
      {onRetry && (
        <Button variant="outline" size="sm" onClick={onRetry}>
          Tentar novamente
        </Button>
      )}
    </div>
  );
}
