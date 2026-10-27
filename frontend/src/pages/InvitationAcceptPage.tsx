import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { Navigate, useParams } from "react-router-dom";
import { toast } from "sonner";
import { z } from "zod";

import { login, register as registerUser } from "@/features/auth/api";
import { useAcceptInvitation, useInvitationPreview } from "@/features/workspaces/hooks";
import { ErrorState } from "@/shared/components/feedback/ErrorState";
import { PasswordInput } from "@/shared/components/forms/PasswordInput";
import { AuthLayout } from "@/shared/components/layout/AuthLayout";
import { Button } from "@/shared/components/ui/button";
import { Input } from "@/shared/components/ui/input";
import { Label } from "@/shared/components/ui/label";
import { Spinner } from "@/shared/components/ui/spinner";
import { useCurrentUser } from "@/shared/hooks/useCurrentUser";
import { getApiErrorMessage } from "@/shared/lib/errors";
import { workspaceRoutes } from "@/shared/lib/routes";
import { useAuthStore } from "@/shared/stores/authStore";

const registerSchema = z.object({
  name: z.string().min(2, "O nome deve ter ao menos 2 caracteres."),
  password: z.string().min(10, "A senha deve ter ao menos 10 caracteres."),
});

type RegisterValues = z.infer<typeof registerSchema>;

function InvitationCopy({
  workspaceName,
  invitedByName,
  role,
}: {
  workspaceName: string;
  invitedByName: string;
  role: string;
}) {
  return (
    <p className="text-sm text-t2">
      <span className="font-medium text-foreground">{invitedByName}</span> convidou você para{" "}
      <span className="font-medium text-foreground">{workspaceName}</span> como{" "}
      <span className="font-medium text-foreground">{role}</span>.
    </p>
  );
}

function RegisterAndAcceptForm({
  token,
  email,
  onDone,
}: {
  token: string;
  email: string;
  onDone: (workspaceId: string) => void;
}) {
  const setAuth = useAuthStore((state) => state.setAuth);
  const acceptInvitation = useAcceptInvitation();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterValues>({ resolver: zodResolver(registerSchema) });

  async function onSubmit(values: RegisterValues) {
    setIsSubmitting(true);
    try {
      await registerUser({ name: values.name, email, password: values.password });
      const result = await login({ email, password: values.password });
      setAuth(result.access_token, result.user);
      const member = await acceptInvitation.mutateAsync(token);
      onDone(member.workspace_id);
    } catch (error) {
      toast.error(getApiErrorMessage(error, "Não foi possível criar a conta e aceitar o convite."));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form className="flex flex-col gap-4" onSubmit={handleSubmit(onSubmit)}>
      <div className="flex flex-col gap-1.5">
        <Label htmlFor="invitation-email">E-mail</Label>
        <Input id="invitation-email" value={email} readOnly disabled />
      </div>
      <div className="flex flex-col gap-1.5">
        <Label htmlFor="invitation-name">Nome completo</Label>
        <Input id="invitation-name" autoComplete="name" {...register("name")} />
        {errors.name && <p className="text-xs text-destructive">{errors.name.message}</p>}
      </div>
      <div className="flex flex-col gap-1.5">
        <Label htmlFor="invitation-password">Senha</Label>
        <PasswordInput
          id="invitation-password"
          autoComplete="new-password"
          {...register("password")}
        />
        {errors.password && <p className="text-xs text-destructive">{errors.password.message}</p>}
      </div>
      <Button type="submit" disabled={isSubmitting}>
        {isSubmitting ? "Criando conta…" : "Criar conta e entrar no workspace"}
      </Button>
    </form>
  );
}

function ConfirmAcceptCard({
  token,
  role,
  onDone,
}: {
  token: string;
  role: string;
  onDone: (workspaceId: string) => void;
}) {
  const acceptInvitation = useAcceptInvitation();

  return (
    <div className="flex justify-center gap-3">
      <Button variant="outline" onClick={() => (window.location.href = "/")}>
        Recusar
      </Button>
      <Button
        disabled={acceptInvitation.isPending}
        onClick={() =>
          acceptInvitation.mutate(token, { onSuccess: (member) => onDone(member.workspace_id) })
        }
      >
        {acceptInvitation.isPending ? "Aceitando…" : `Aceitar como ${role}`}
      </Button>
    </div>
  );
}

export function InvitationAcceptPage() {
  const { token } = useParams<{ token: string }>();
  const accessToken = useAuthStore((state) => state.accessToken);
  const { data: profile, refetch: refetchProfile } = useCurrentUser();
  const { data: preview, isLoading, isError } = useInvitationPreview(token);
  const [accepted, setAccepted] = useState<{ workspaceId: string } | null>(null);

  if (accepted) {
    const workspace = profile?.workspaces.find((w) => w.id === accepted.workspaceId);
    if (workspace) {
      return <Navigate to={workspaceRoutes.issues(workspace.slug)} replace />;
    }
  }

  function handleAccepted(workspaceId: string) {
    refetchProfile().then(() => setAccepted({ workspaceId }));
  }

  return (
    <AuthLayout>
      {isLoading ? (
        <div className="flex flex-col items-center gap-3 text-center">
          <Spinner className="size-6" />
          <p className="text-sm text-muted-foreground">Carregando convite…</p>
        </div>
      ) : isError || !preview ? (
        <ErrorState message="Este link de convite é inválido." />
      ) : preview.status !== "PENDING" ? (
        <div className="flex flex-col items-center gap-2 text-center">
          <h1 className="font-heading text-xl font-semibold">
            {preview.status === "ACCEPTED" ? "Convite já aceito" : "Convite expirado"}
          </h1>
          <p className="max-w-xs text-sm text-t2">
            {preview.status === "ACCEPTED"
              ? "Este convite já foi aceito anteriormente."
              : "Peça para quem convidou reenviar um novo link."}
          </p>
        </div>
      ) : (
        <div className="flex w-full max-w-sm flex-col items-center gap-6">
          <div className="flex flex-col items-center gap-2 text-center">
            <h1 className="font-heading text-xl font-semibold tracking-tight">
              Convite para {preview.workspace_name}
            </h1>
            <InvitationCopy
              workspaceName={preview.workspace_name}
              invitedByName={preview.invited_by_name}
              role={preview.role}
            />
          </div>

          {accessToken ? (
            profile && profile.email.toLowerCase() === preview.email.toLowerCase() ? (
              <ConfirmAcceptCard
                token={token as string}
                role={preview.role}
                onDone={handleAccepted}
              />
            ) : (
              <ErrorState
                message={`Este convite foi emitido para ${preview.email}, não para sua conta atual.`}
              />
            )
          ) : (
            <div className="w-full rounded-xl border border-border bg-panel p-5">
              <RegisterAndAcceptForm
                token={token as string}
                email={preview.email}
                onDone={handleAccepted}
              />
            </div>
          )}
        </div>
      )}
    </AuthLayout>
  );
}
