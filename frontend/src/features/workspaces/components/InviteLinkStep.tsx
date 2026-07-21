import { Check, Copy } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { Button } from "@/shared/components/ui/button";
import {
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/shared/components/ui/dialog";
import { Input } from "@/shared/components/ui/input";
import { invitationAcceptRoute } from "@/shared/lib/routes";

import type { InvitationCreatedResult } from "../types";

export function InviteLinkStep({
  invitation,
  onDone,
}: {
  invitation: InvitationCreatedResult;
  onDone: () => void;
}) {
  const [copied, setCopied] = useState(false);
  const link = `${window.location.origin}${invitationAcceptRoute(invitation.token)}`;

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(link);
      setCopied(true);
      toast.success("Link copiado.");
    } catch {
      toast.error("Não foi possível copiar o link.");
    }
  }

  return (
    <>
      <DialogHeader>
        <DialogTitle>Convite pronto</DialogTitle>
        <DialogDescription>
          Ainda não enviamos e-mails automaticamente — compartilhe este link com {invitation.email}.
          Ele só é exibido uma vez.
        </DialogDescription>
      </DialogHeader>
      <div className="flex items-center gap-2 py-4">
        <Input readOnly value={link} className="font-mono text-xs" />
        <Button
          type="button"
          variant="outline"
          size="icon"
          onClick={handleCopy}
          aria-label="Copiar link"
        >
          {copied ? <Check className="size-4" /> : <Copy className="size-4" />}
        </Button>
      </div>
      <DialogFooter>
        <Button type="button" onClick={onDone}>
          Concluído
        </Button>
      </DialogFooter>
    </>
  );
}
