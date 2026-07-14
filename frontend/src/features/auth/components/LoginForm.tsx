import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { z } from "zod";

import { Button } from "@/shared/components/ui/button";
import { Input } from "@/shared/components/ui/input";
import { Label } from "@/shared/components/ui/label";
import { useAuthStore } from "@/shared/stores/authStore";

import { login, register as registerUser } from "../api";

const loginSchema = z.object({
  email: z.string().min(1, "Informe o e-mail.").email("E-mail inválido."),
  password: z.string().min(1, "Informe a senha."),
});

const registerSchema = z.object({
  name: z.string().min(2, "O nome deve ter ao menos 2 caracteres."),
  email: z.string().min(1, "Informe o e-mail.").email("E-mail inválido."),
  password: z.string().min(10, "A senha deve ter ao menos 10 caracteres."),
});

type LoginValues = z.infer<typeof loginSchema>;
type RegisterValues = z.infer<typeof registerSchema>;

function LoginTab() {
  const navigate = useNavigate();
  const setAuth = useAuthStore((state) => state.setAuth);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginValues>({ resolver: zodResolver(loginSchema) });

  async function onSubmit(values: LoginValues) {
    setIsSubmitting(true);
    try {
      const result = await login(values);
      setAuth(result.access_token, result.user);
      navigate("/", { replace: true });
    } catch {
      toast.error("E-mail ou senha inválidos.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form className="flex flex-col gap-4" onSubmit={handleSubmit(onSubmit)}>
      <div className="flex flex-col gap-1.5">
        <Label htmlFor="login-email">E-mail</Label>
        <Input id="login-email" type="email" autoComplete="email" {...register("email")} />
        {errors.email && <p className="text-xs text-destructive">{errors.email.message}</p>}
      </div>
      <div className="flex flex-col gap-1.5">
        <Label htmlFor="login-password">Senha</Label>
        <Input
          id="login-password"
          type="password"
          autoComplete="current-password"
          {...register("password")}
        />
        {errors.password && <p className="text-xs text-destructive">{errors.password.message}</p>}
      </div>
      <Button type="submit" disabled={isSubmitting}>
        {isSubmitting ? "Entrando…" : "Entrar"}
      </Button>
    </form>
  );
}

function RegisterTab({ onRegistered }: { onRegistered: (email: string) => void }) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterValues>({ resolver: zodResolver(registerSchema) });

  async function onSubmit(values: RegisterValues) {
    setIsSubmitting(true);
    try {
      await registerUser(values);
      toast.success("Conta criada. Faça login para continuar.");
      onRegistered(values.email);
    } catch {
      toast.error("Não foi possível criar a conta. O e-mail já pode estar em uso.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form className="flex flex-col gap-4" onSubmit={handleSubmit(onSubmit)}>
      <div className="flex flex-col gap-1.5">
        <Label htmlFor="register-name">Nome</Label>
        <Input id="register-name" autoComplete="name" {...register("name")} />
        {errors.name && <p className="text-xs text-destructive">{errors.name.message}</p>}
      </div>
      <div className="flex flex-col gap-1.5">
        <Label htmlFor="register-email">E-mail</Label>
        <Input id="register-email" type="email" autoComplete="email" {...register("email")} />
        {errors.email && <p className="text-xs text-destructive">{errors.email.message}</p>}
      </div>
      <div className="flex flex-col gap-1.5">
        <Label htmlFor="register-password">Senha</Label>
        <Input
          id="register-password"
          type="password"
          autoComplete="new-password"
          {...register("password")}
        />
        {errors.password && <p className="text-xs text-destructive">{errors.password.message}</p>}
        <p className="text-xs text-muted-foreground">
          Ao menos 10 caracteres, com maiúscula, minúscula, número e símbolo.
        </p>
      </div>
      <Button type="submit" disabled={isSubmitting}>
        {isSubmitting ? "Criando conta…" : "Criar conta"}
      </Button>
    </form>
  );
}

export function LoginForm() {
  const [mode, setMode] = useState<"login" | "register">("login");

  return (
    <div className="flex flex-col gap-4">
      <div className="flex gap-1 rounded-lg bg-muted p-1">
        <button
          type="button"
          onClick={() => setMode("login")}
          className={`flex-1 rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
            mode === "login" ? "bg-background shadow-sm" : "text-muted-foreground"
          }`}
        >
          Entrar
        </button>
        <button
          type="button"
          onClick={() => setMode("register")}
          className={`flex-1 rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
            mode === "register" ? "bg-background shadow-sm" : "text-muted-foreground"
          }`}
        >
          Criar conta
        </button>
      </div>
      {mode === "login" ? <LoginTab /> : <RegisterTab onRegistered={() => setMode("login")} />}
    </div>
  );
}
