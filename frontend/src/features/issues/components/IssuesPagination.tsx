import { ChevronLeft, ChevronRight } from "lucide-react";

import { Button } from "@/shared/components/ui/button";
import type { PaginationMeta } from "@/shared/lib/apiTypes";

export function IssuesPagination({
  meta,
  onPageChange,
}: {
  meta: PaginationMeta;
  onPageChange: (page: number) => void;
}) {
  if (meta.total_pages <= 1) {
    return null;
  }

  return (
    <div className="flex items-center justify-between text-sm text-muted-foreground">
      <span>
        Página {meta.page} de {meta.total_pages} · {meta.total} issue
        {meta.total === 1 ? "" : "s"}
      </span>
      <div className="flex items-center gap-1">
        <Button
          variant="outline"
          size="icon-sm"
          disabled={meta.page <= 1}
          onClick={() => onPageChange(meta.page - 1)}
          aria-label="Página anterior"
        >
          <ChevronLeft />
        </Button>
        <Button
          variant="outline"
          size="icon-sm"
          disabled={meta.page >= meta.total_pages}
          onClick={() => onPageChange(meta.page + 1)}
          aria-label="Próxima página"
        >
          <ChevronRight />
        </Button>
      </div>
    </div>
  );
}
