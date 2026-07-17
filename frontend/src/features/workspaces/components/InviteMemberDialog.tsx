import { zodResolver } from "@hookform/resolvers/zod";
import { Check, Copy } from "lucide-react";
import { useState } from "react";
import { Controller, useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

import { Button } from "@/shared/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/shared/components/ui/dialog";
import { Input } from "@/shared/components/ui/input";
import { Label } from "@/shared/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/shared/components/ui/select";
import { invitationAcceptRoute } from "@/shared/lib/routes";

import { useCreateInvitation } from "../hooks";
import type { InvitationCreatedResult } from "../types";

const schema = z.object({
  email: z.string().email("Informe um e-mail válido."),
  role: z.enum(["ADMIN", "MEMBER", "GUEST"]),
});

type Values = z.infer<typeof schema>;

function InviteLinkStep({
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
        <DialogTitle>Convite criado</DialogTitle>
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

export function InviteMemberDialog({ workspaceId }: { workspaceId: string }) {
  const [open, setOpen] = useState(false);
  const [created, setCreated] = useState<InvitationCreatedResult | null>(null);
  const createInvitation = useCreateInvitation(workspaceId);
  const {
    register,
    handleSubmit,
    control,
    reset,
    formState: { errors },
  } = useForm<Values>({ resolver: zodResolver(schema), defaultValues: { role: "MEMBER" } });

  function handleOpenChange(next: boolean) {
    setOpen(next);
    if (!next) {
      reset();
      setCreated(null);
    }
  }

  async function onSubmit(values: Values) {
    const invitation = await createInvitation.mutateAsync(values);
    setCreated(invitation);
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogTrigger asChild>
        <Button>Convidar membro</Button>
      </DialogTrigger>
      <DialogContent>
        {created ? (
          <InviteLinkStep invitation={created} onDone={() => handleOpenChange(false)} />
        ) : (
          <form onSubmit={handleSubmit(onSubmit)}>
            <DialogHeader>
              <DialogTitle>Convidar membro</DialogTitle>
              <DialogDescription>
                Convide alguém para este workspace por e-mail, com um papel inicial.
              </DialogDescription>
            </DialogHeader>
            <div className="flex flex-col gap-4 py-4">
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="invite-email">E-mail</Label>
                <Input
                  id="invite-email"
                  type="email"
                  placeholder="pessoa@empresa.com"
                  {...register("email")}
                />
                {errors.email && <p className="text-xs text-destructive">{errors.email.message}</p>}
              </div>
              <div className="flex flex-col gap-1.5">
                <Label>Papel</Label>
                <Controller
                  control={control}
                  name="role"
                  render={({ field }) => (
                    <Select value={field.value} onValueChange={field.onChange}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="ADMIN">Admin</SelectItem>
                        <SelectItem value="MEMBER">Member</SelectItem>
                        <SelectItem value="GUEST">Guest</SelectItem>
                      </SelectContent>
                    </Select>
                  )}
                />
              </div>
            </div>
            <DialogFooter>
              <Button type="submit" disabled={createInvitation.isPending}>
                {createInvitation.isPending ? "Criando…" : "Criar convite"}
              </Button>
            </DialogFooter>
          </form>
        )}
      </DialogContent>
    </Dialog>
  );
}
