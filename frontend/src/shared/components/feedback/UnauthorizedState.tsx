import { LogIn } from "lucide-react";
import { Link } from "react-router-dom";

import { Button } from "@/shared/components/ui/button";

/**
 * Estado "sessão expirada"/401 — presentacional apenas. `httpClient.ts` já resolve
 * silenciosamente o 401 mais comum (access token expirado) via refresh automático;
 * este componente é para o caso em que isso falhou e uma tela precisa comunicar o
 * motivo, em vez de redirecionar direto (decisão de UX da Sprint 9).
 */
export function UnauthorizedState() {
  return (
    <div className="flex flex-col items-center gap-3 py-16 text-center">
      <LogIn className="size-8 text-muted-foreground" />
      <p className="text-sm font-medium">Sua sessão expirou.</p>
      <p className="text-sm text-muted-foreground">Entre novamente para continuar.</p>
      <Button asChild size="sm">
        <Link to="/login">Entrar</Link>
      </Button>
    </div>
  );
}
