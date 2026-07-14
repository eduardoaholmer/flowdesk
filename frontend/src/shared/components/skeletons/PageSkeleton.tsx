import { Skeleton } from "@/shared/components/ui/skeleton";

/** Casca de carregamento para uma página de detalhe (título + linhas de corpo). */
export function PageSkeleton() {
  return (
    <div className="flex flex-col gap-3">
      <Skeleton className="h-8 w-64" />
      <Skeleton className="h-4 w-full max-w-md" />
      <Skeleton className="h-4 w-full max-w-sm" />
    </div>
  );
}
