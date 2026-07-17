import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { Link } from "react-router-dom";
import { toast } from "sonner";
import { z } from "zod";

import { Button } from "@/shared/components/ui/button";
import { Input } from "@/shared/components/ui/input";
import { Label } from "@/shared/components/ui/label";
import { getApiErrorMessage } from "@/shared/lib/errors";

import { requestPasswordReset } from "../api";

const schema = z.object({
  email: z.string().min(1, "Informe o e-mail.").email("E-mail inválido."),
});

type FormValues = z.infer<typeof schema>;

/**
 * Sempre transiciona para o estado de sucesso após um 202 — o backend nunca
 * distingue e-mail existente de inexistente (anti-enumeration,
 * docs/07-security.md §10). Um erro real (rede, 429 rate limit) é a única
 * exceção: aí sim mostramos o problema em vez de fingir sucesso.
 */
export function ForgotPasswordForm() {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submittedEmail, setSubmittedEmail] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  async function onSubmit(values: FormValues) {
    setIsSubmitting(true);
    try {
      await requestPasswordReset(values.email);
      setSubmittedEmail(values.email);
    } catch (error) {
      toast.error(getApiErrorMessage(error));
    } finally {
      setIsSubmitting(false);
    }
  }

  if (submittedEmail) {
    return (
      <div className="flex flex-col gap-4 text-sm">
        <p>
          Se <span className="font-medium">{submittedEmail}</span> tiver uma conta, enviamos um link
          de redefinição de senha para ele.
        </p>
        <Link to="/login" className="font-medium text-primary hover:underline">
          Voltar para o login
        </Link>
      </div>
    );
  }

  return (
    <form className="flex flex-col gap-4" onSubmit={handleSubmit(onSubmit)}>
      <div className="flex flex-col gap-1.5">
        <Label htmlFor="forgot-password-email">E-mail</Label>
        <Input
          id="forgot-password-email"
          type="email"
          autoComplete="email"
          {...register("email")}
        />
        {errors.email && <p className="text-xs text-destructive">{errors.email.message}</p>}
      </div>
      <Button type="submit" disabled={isSubmitting}>
        {isSubmitting ? "Enviando…" : "Enviar link de redefinição"}
      </Button>
      <Link to="/login" className="text-center text-sm text-muted-foreground hover:underline">
        Voltar para o login
      </Link>
    </form>
  );
}
