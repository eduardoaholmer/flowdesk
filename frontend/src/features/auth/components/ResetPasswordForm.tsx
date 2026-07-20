import { zodResolver } from "@hookform/resolvers/zod";
import { isAxiosError } from "axios";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { useNavigate, Link } from "react-router-dom";
import { toast } from "sonner";
import { z } from "zod";

import { Button } from "@/shared/components/ui/button";
import { Label } from "@/shared/components/ui/label";
import { PasswordInput } from "@/shared/components/forms/PasswordInput";
import { getApiErrorMessage } from "@/shared/lib/errors";

import { confirmPasswordReset } from "../api";

const schema = z
  .object({
    password: z.string().min(10, "A senha deve ter ao menos 10 caracteres."),
    confirmPassword: z.string().min(1, "Confirme a nova senha."),
  })
  .refine((values) => values.password === values.confirmPassword, {
    message: "As senhas não coincidem.",
    path: ["confirmPassword"],
  });

type FormValues = z.infer<typeof schema>;

export function ResetPasswordForm({ token }: { token: string }) {
  const navigate = useNavigate();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isTokenInvalid, setIsTokenInvalid] = useState(false);
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  async function onSubmit(values: FormValues) {
    setIsSubmitting(true);
    try {
      await confirmPasswordReset({ token, new_password: values.password });
      toast.success("Senha redefinida. Faça login com a nova senha.");
      navigate("/login", { replace: true });
    } catch (error) {
      if (isAxiosError(error) && error.response?.status === 401) {
        setIsTokenInvalid(true);
      } else {
        toast.error(getApiErrorMessage(error));
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  if (isTokenInvalid) {
    return (
      <div className="flex flex-col gap-4 text-sm">
        <p>Este link de redefinição é inválido ou expirou.</p>
        <Link to="/forgot-password" className="font-medium text-primary hover:underline">
          Solicitar um novo link
        </Link>
      </div>
    );
  }

  return (
    <form className="flex flex-col gap-4" onSubmit={handleSubmit(onSubmit)}>
      <div className="flex flex-col gap-1.5">
        <Label htmlFor="reset-password-password">Nova senha</Label>
        <PasswordInput
          id="reset-password-password"
          autoComplete="new-password"
          {...register("password")}
        />
        {errors.password && <p className="text-xs text-destructive">{errors.password.message}</p>}
        <p className="text-xs text-muted-foreground">
          Ao menos 10 caracteres, com maiúscula, minúscula, número e símbolo.
        </p>
      </div>
      <div className="flex flex-col gap-1.5">
        <Label htmlFor="reset-password-confirm">Confirmar nova senha</Label>
        <PasswordInput
          id="reset-password-confirm"
          autoComplete="new-password"
          {...register("confirmPassword")}
        />
        {errors.confirmPassword && (
          <p className="text-xs text-destructive">{errors.confirmPassword.message}</p>
        )}
      </div>
      <Button type="submit" disabled={isSubmitting}>
        {isSubmitting ? "Redefinindo…" : "Redefinir senha"}
      </Button>
    </form>
  );
}
