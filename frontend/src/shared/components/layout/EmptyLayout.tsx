import type { ReactNode } from "react";

export function EmptyLayout({ children }: { children: ReactNode }) {
  return <div className="mx-auto flex max-w-sm flex-col gap-4 pt-12">{children}</div>;
}
