import { useWorkflowStates } from "@/features/workflow-states/hooks";
import { ErrorState } from "@/shared/components/feedback/ErrorState";
import { ListSkeleton } from "@/shared/components/skeletons/ListSkeleton";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/shared/components/ui/select";

import { useGitHubAutomations, useSetGitHubAutomation } from "../hooks";
import type { GitHubAutomationEvent } from "../types";

const EVENT_LABELS: Record<GitHubAutomationEvent, { title: string; hint: string }> = {
  PR_DRAFT: { title: "PR em rascunho", hint: "Aberto como rascunho ou convertido em rascunho." },
  PR_OPEN: { title: "PR aberto", hint: "Aberto, reaberto ou marcado como pronto para revisão." },
  PR_MERGED: { title: "PR mergeado", hint: "Fechado com merge." },
  PR_CLOSED: { title: "PR fechado sem merge", hint: "Fechado sem merge." },
};

// O `Select` do Radix não aceita `value=""`: "sem ação" precisa de um valor próprio.
const NO_ACTION = "__none__";

/** Para qual status as issues citadas por um PR vão em cada situação do PR. Issues
 * já concluídas ou canceladas nunca são movidas (regra do backend). */
export function GitHubAutomationRules({ workspaceId }: { workspaceId: string }) {
  const rules = useGitHubAutomations(workspaceId);
  const { data: workflowStates } = useWorkflowStates(workspaceId);
  const setRule = useSetGitHubAutomation(workspaceId);

  return (
    <div className="flex flex-col gap-3">
      <div>
        <h3 className="font-heading text-base font-semibold tracking-tight">Automação de status</h3>
        <p className="text-sm text-t2">
          Move as issues citadas por um pull request (<code>FD-123</code> na branch, no título ou na
          descrição). Issues concluídas ou canceladas nunca são movidas.
        </p>
      </div>

      {rules.isLoading ? (
        <ListSkeleton rows={4} />
      ) : rules.isError || !rules.data ? (
        <ErrorState
          message="Não foi possível carregar as regras de automação."
          onRetry={() => rules.refetch()}
        />
      ) : (
        <div className="rounded-xl border border-border bg-panel px-4">
          {rules.data.map((rule) => {
            const label = EVENT_LABELS[rule.event];
            return (
              <div
                key={rule.event}
                className="flex flex-col gap-2 border-b py-3 last:border-b-0 sm:flex-row sm:items-center sm:justify-between"
              >
                <div className="min-w-0">
                  <p className="text-sm font-medium">{label.title}</p>
                  <p className="text-xs text-muted-foreground">{label.hint}</p>
                </div>
                <Select
                  value={rule.target_state_id ?? NO_ACTION}
                  disabled={setRule.isPending}
                  onValueChange={(value) =>
                    setRule.mutate({
                      event: rule.event,
                      target_state_id: value === NO_ACTION ? null : value,
                    })
                  }
                >
                  <SelectTrigger size="sm" className="w-full sm:w-48" aria-label={label.title}>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value={NO_ACTION}>Sem ação</SelectItem>
                    {(workflowStates ?? []).map((state) => (
                      <SelectItem key={state.id} value={state.id}>
                        {state.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
