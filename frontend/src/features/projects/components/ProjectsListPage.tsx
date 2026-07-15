import { useState } from "react";
import { useSearchParams } from "react-router-dom";

import { ErrorState } from "@/shared/components/feedback/ErrorState";
import { Pagination } from "@/shared/components/navigation/Pagination";
import { ListSkeleton } from "@/shared/components/skeletons/ListSkeleton";
import { useDebouncedValue } from "@/shared/hooks/useDebouncedValue";
import { cn } from "@/shared/lib/utils";

import { useProjects } from "../hooks";
import type { ProjectStatus } from "../types";
import { ProjectsEmptyState } from "./ProjectsEmptyState";
import { ProjectsTable } from "./ProjectsTable";
import { ProjectsToolbar } from "./ProjectsToolbar";

const PER_PAGE = 20;

export function ProjectsListPage({
  workspaceId,
  workspaceSlug,
}: {
  workspaceId: string;
  workspaceSlug: string;
}) {
  const [searchParams, setSearchParams] = useSearchParams();
  const [searchInput, setSearchInput] = useState(searchParams.get("search") ?? "");
  const debouncedSearch = useDebouncedValue(searchInput);

  const page = Number(searchParams.get("page") ?? "1");
  const status = (searchParams.get("status") as ProjectStatus | null) ?? "ALL";

  const { data, isLoading, isError, refetch, isPlaceholderData } = useProjects(workspaceId, {
    page,
    per_page: PER_PAGE,
    search: debouncedSearch || undefined,
    status: status === "ALL" ? undefined : status,
    sort: "-created_at",
  });

  function updateParams(next: { search?: string; status?: ProjectStatus | "ALL"; page?: number }) {
    setSearchParams((prev) => {
      const params = new URLSearchParams(prev);
      if (next.search !== undefined) {
        if (next.search) params.set("search", next.search);
        else params.delete("search");
        params.delete("page");
      }
      if (next.status !== undefined) {
        if (next.status !== "ALL") params.set("status", next.status);
        else params.delete("status");
        params.delete("page");
      }
      if (next.page !== undefined) {
        if (next.page > 1) params.set("page", String(next.page));
        else params.delete("page");
      }
      return params;
    });
  }

  return (
    <div className="flex flex-col gap-4">
      <div>
        <h1 className="text-lg font-semibold">Projetos</h1>
        <p className="text-sm text-muted-foreground">Projetos deste workspace.</p>
      </div>

      <ProjectsToolbar
        workspaceId={workspaceId}
        search={searchInput}
        onSearchChange={(value) => {
          setSearchInput(value);
          updateParams({ search: value });
        }}
        status={status}
        onStatusChange={(value) => updateParams({ status: value })}
      />

      {isLoading ? (
        <ListSkeleton rows={5} />
      ) : isError ? (
        <ErrorState message="Não foi possível carregar os projetos." onRetry={() => refetch()} />
      ) : data && data.data.length > 0 ? (
        <div className={cn("flex flex-col gap-4", isPlaceholderData && "opacity-60")}>
          <ProjectsTable
            workspaceId={workspaceId}
            workspaceSlug={workspaceSlug}
            projects={data.data}
          />
          <Pagination
            meta={data.meta}
            itemLabel="projeto"
            onPageChange={(next) => updateParams({ page: next })}
          />
        </div>
      ) : (
        <ProjectsEmptyState
          workspaceId={workspaceId}
          hasFilters={Boolean(debouncedSearch) || status !== "ALL"}
        />
      )}
    </div>
  );
}
