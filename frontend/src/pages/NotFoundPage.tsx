import { Link } from "react-router-dom";

import { NotFoundState } from "@/shared/components/feedback/NotFoundState";
import { Button } from "@/shared/components/ui/button";

export function NotFoundPage() {
  return (
    <div className="flex h-full items-center justify-center">
      <NotFoundState
        action={
          <Button asChild>
            <Link to="/">Voltar para o início</Link>
          </Button>
        }
      />
    </div>
  );
}
