import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm, useWatch } from "react-hook-form";
import { Link, useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { z } from "zod";

import { Button } from "@/shared/components/ui/button";
import { Input } from "@/shared/components/ui/input";
import { Label } from "@/shared/components/ui/label";
import { PasswordInput } from "@/shared/components/forms/PasswordInput";
import { cn } from "@/shared/lib/utils";
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

/** Mesmo cálculo de `Autenticacao.dc.html::passStrength` — 3 níveis (tamanho,
 * mistura letra+número, símbolo), puramente visual/informativo. A validação
 * real de força continua no backend (`_validate_strong_password`); isto nunca
 * bloqueia o submit, só dá feedback progressivo enquanto a pessoa digita. */
function passwordStrength(password: string): number {
  let strength = 0;
  if (password.length >= 8) strength++;
  if (/[0-9]/.test(password) && /[A-Za-z]/.test(password)) strength++;
  if (/[^A-Za-z0-9]/.test(password)) strength++;
  return strength;
}

const STRENGTH_LABEL = [
  "Use letras, números e um símbolo",
  "Senha fraca",
  "Senha razoável",
  "Senha forte",
];
const STRENGTH_COLOR = ["bg-border", "bg-destructive", "bg-amber", "bg-green"];

function PasswordStrengthMeter({ password }: { password: string }) {
  const strength = passwordStrength(password);
  return (
    <div className="flex flex-col gap-1">
      <div className="flex gap-1">
        {[0, 1, 2].map((i) => (
          <span
            key={i}
            className={cn(
              "h-[3px] flex-1 rounded-full",
              strength > i ? STRENGTH_COLOR[strength] : "bg-border",
            )}
          />
        ))}
      </div>
      <p className="text-xs text-t3">{password ? STRENGTH_LABEL[strength] : STRENGTH_LABEL[0]}</p>
    </div>
  );
}

function LoginTab({ redirectTo }: { redirectTo: string }) {
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
      navigate(redirectTo, { replace: true });
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
        <div className="flex items-center justify-between">
          <Label htmlFor="login-password">Senha</Label>
          <Link to="/forgot-password" className="text-xs text-t3 hover:underline">
            Esqueci minha senha
          </Link>
        </div>
        <PasswordInput
          id="login-password"
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
    control,
    formState: { errors },
  } = useForm<RegisterValues>({ resolver: zodResolver(registerSchema) });
  const password = useWatch({ control, name: "password" }) ?? "";

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
        <PasswordInput
          id="register-password"
          autoComplete="new-password"
          {...register("password")}
        />
        {errors.password && <p className="text-xs text-destructive">{errors.password.message}</p>}
        <PasswordStrengthMeter password={password} />
      </div>
      <Button type="submit" disabled={isSubmitting}>
        {isSubmitting ? "Criando conta…" : "Criar conta"}
      </Button>
    </form>
  );
}

const COPY = {
  login: { title: "Bem-vinda de volta", subtitle: "Entre para ver o estado real do trabalho." },
  register: {
    title: "Crie sua conta",
    subtitle: "Da conta à primeira issue em menos de dois minutos.",
  },
};

export function LoginForm({ redirectTo = "/" }: { redirectTo?: string }) {
  const [mode, setMode] = useState<"login" | "register">("login");

  return (
    <div className="flex flex-col gap-6">
      <div className="text-center">
        <h1 className="font-heading text-2xl font-semibold tracking-tight">{COPY[mode].title}</h1>
        <p className="mt-1.5 text-sm text-t2">{COPY[mode].subtitle}</p>
      </div>
      <div className="rounded-xl border border-border bg-panel p-6 shadow-sm">
        <div className="mb-4 flex gap-1 rounded-lg bg-muted p-1">
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
        {mode === "login" ? (
          <LoginTab redirectTo={redirectTo} />
        ) : (
          <RegisterTab onRegistered={() => setMode("login")} />
        )}
      </div>
    </div>
  );
}
