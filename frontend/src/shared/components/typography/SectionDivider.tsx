import { Separator } from "@/shared/components/ui/separator";
import { cn } from "@/shared/lib/utils";

interface SectionDividerProps {
  /** Rótulo opcional centralizado sobre a linha (ex.: "ou"). Sem label, é só uma régua horizontal. */
  label?: string;
  className?: string;
}

/** Ritmo vertical consistente entre seções de uma página — wrapper fino sobre `ui/separator.tsx`. */
export function SectionDivider({ label, className }: SectionDividerProps) {
  if (!label) {
    return <Separator className={cn("my-6", className)} />;
  }

  return (
    <div className={cn("relative my-6", className)}>
      <Separator />
      <span className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-background px-2 text-xs text-muted-foreground">
        {label}
      </span>
    </div>
  );
}
