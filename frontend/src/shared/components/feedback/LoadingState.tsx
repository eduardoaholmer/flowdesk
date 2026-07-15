import { Spinner } from "@/shared/components/ui/spinner";

interface LoadingStateProps {
  message?: string;
}

/**
 * Estado de carregamento em tela cheia/bloco (não a linha de skeleton de uma lista —
 * ver `shared/components/skeletons/`). `role="status"`/`aria-live="polite"` anuncia
 * a leitores de tela sem roubar foco.
 */
export function LoadingState({ message = "Carregando…" }: LoadingStateProps) {
  return (
    <div
      role="status"
      aria-live="polite"
      className="flex flex-col items-center gap-3 py-16 text-center"
    >
      <Spinner className="size-6" />
      <p className="text-sm text-muted-foreground">{message}</p>
    </div>
  );
}
