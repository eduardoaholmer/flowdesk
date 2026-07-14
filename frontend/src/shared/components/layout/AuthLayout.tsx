import type { ReactNode } from "react";

export function AuthLayout({ children }: { children: ReactNode }) {
  return <div className="flex min-h-screen items-center justify-center p-4">{children}</div>;
}
