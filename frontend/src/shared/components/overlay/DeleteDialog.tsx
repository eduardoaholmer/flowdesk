import type { ReactNode } from "react";

import { ConfirmActionDialog } from "@/shared/components/overlay/ConfirmActionDialog";

interface DeleteDialogProps {
  trigger: ReactNode;
  title: string;
  description: string;
  onConfirm: () => void;
  isPending?: boolean;
}

/** Preset destrutivo de `ConfirmActionDialog` para o fluxo mais comum do app: excluir algo. */
export function DeleteDialog({
  trigger,
  title,
  description,
  onConfirm,
  isPending,
}: DeleteDialogProps) {
  return (
    <ConfirmActionDialog
      trigger={trigger}
      title={title}
      description={description}
      confirmLabel="Excluir"
      destructive
      isPending={isPending}
      onConfirm={onConfirm}
    />
  );
}
