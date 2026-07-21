import { useState } from "react";
import type { ReactNode } from "react";

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/shared/components/ui/alert-dialog";
import { Input } from "@/shared/components/ui/input";

/** Mesma forma de `ConfirmActionDialog`, para a única ação do produto grave
 * o bastante para exigir digitar um valor (não só clicar) antes de confirmar
 * — hoje só a exclusão de workspace (`Administracao.dc.html`, M7). */
export function TypeToConfirmDialog({
  trigger,
  title,
  description,
  confirmText,
  confirmLabel,
  onConfirm,
  isPending,
}: {
  trigger: ReactNode;
  title: string;
  description: string;
  confirmText: string;
  confirmLabel: string;
  onConfirm: () => void;
  isPending?: boolean;
}) {
  const [open, setOpen] = useState(false);
  const [value, setValue] = useState("");
  const canConfirm = value === confirmText;

  return (
    <AlertDialog
      open={open}
      onOpenChange={(next) => {
        setOpen(next);
        if (!next) setValue("");
      }}
    >
      <AlertDialogTrigger asChild>{trigger}</AlertDialogTrigger>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>{title}</AlertDialogTitle>
          <AlertDialogDescription>{description}</AlertDialogDescription>
        </AlertDialogHeader>
        <div className="flex flex-col gap-1.5">
          <label htmlFor="type-to-confirm-input" className="text-sm text-muted-foreground">
            Digite <span className="font-mono font-semibold text-foreground">{confirmText}</span>{" "}
            para confirmar:
          </label>
          <Input
            id="type-to-confirm-input"
            value={value}
            onChange={(event) => setValue(event.target.value)}
            placeholder={confirmText}
            autoComplete="off"
          />
        </div>
        <AlertDialogFooter>
          <AlertDialogCancel disabled={isPending}>Cancelar</AlertDialogCancel>
          <AlertDialogAction
            variant="destructive"
            disabled={!canConfirm || isPending}
            onClick={onConfirm}
          >
            {confirmLabel}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
