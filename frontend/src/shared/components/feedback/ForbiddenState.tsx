import { ShieldAlert } from "lucide-react";

interface ForbiddenStateProps {
  description?: string;
}

/** Estado 403 — usuário autenticado, mas sem permissão para o recurso. Presentacional apenas. */
export function ForbiddenState({
  description = "Você não tem permissão para acessar este recurso.",
}: ForbiddenStateProps) {
  return (
    <div className="flex flex-col items-center gap-3 py-16 text-center">
      <ShieldAlert className="size-8 text-muted-foreground" />
      <p className="text-sm font-medium">Acesso negado</p>
      <p className="text-sm text-muted-foreground">{description}</p>
    </div>
  );
}
