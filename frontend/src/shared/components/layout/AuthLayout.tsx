import type { ReactNode } from "react";

import { Logo } from "@/shared/components/brand/Logo";
import { ThemeToggle } from "@/shared/components/ThemeToggle";

export function AuthLayout({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-screen flex-col bg-background">
      <header className="flex items-center justify-between px-7 py-5">
        <Logo size="sm" />
        <ThemeToggle />
      </header>
      <div className="flex flex-1 items-center justify-center p-4 pb-20">{children}</div>
    </div>
  );
}
