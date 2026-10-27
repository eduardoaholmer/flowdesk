import { Check, GitBranch } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { Button } from "@/shared/components/ui/button";

import { issueBranchName } from "../branchName";

/** Copia `fd-123-titulo` — o PR aberto a partir dessa branch já nasce vinculado à
 * issue quando o GitHub está conectado ao workspace. */
export function CopyBranchNameButton({ identifier, title }: { identifier: string; title: string }) {
  const [copied, setCopied] = useState(false);

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(issueBranchName(identifier, title));
      setCopied(true);
      toast.success("Nome da branch copiado.");
      setTimeout(() => setCopied(false), 1500);
    } catch {
      toast.error("Não foi possível copiar o nome da branch.");
    }
  }

  return (
    <Button variant="ghost" size="icon-sm" aria-label="Copiar nome da branch" onClick={handleCopy}>
      {copied ? <Check /> : <GitBranch />}
    </Button>
  );
}
