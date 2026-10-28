import { Plug } from "lucide-react";

import { useWorkspaceMembers } from "@/features/workspaces/hooks";
import { EmptyState } from "@/shared/components/feedback/EmptyState";
import { ErrorState } from "@/shared/components/feedback/ErrorState";
import { GitHubIcon } from "@/shared/components/icons/ProviderIcons";
import { ConfirmActionDialog } from "@/shared/components/overlay/ConfirmActionDialog";
import { ListSkeleton } from "@/shared/components/skeletons/ListSkeleton";
import { Badge } from "@/shared/components/ui/badge";
import { Button } from "@/shared/components/ui/button";
import { formatDate } from "@/shared/lib/date";

import { useConnectGitHub, useDisconnectGitHubInstallation, useGitHubIntegration } from "../hooks";
import type { GitHubInstallation } from "../types";
import { GitHubAutomationRules } from "./GitHubAutomationRules";

function InstallationRow({
  installation,
  connectedByName,
  workspaceId,
}: {
  installation: GitHubInstallation;
  connectedByName: string;
  workspaceId: string;
}) {
  const disconnect = useDisconnectGitHubInstallation(workspaceId);

  return (
    <div className="flex items-center gap-3 border-b py-3 last:border-b-0">
      <GitHubIcon className="size-5 shrink-0" />
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium">{installation.account_login}</p>
        <p className="text-xs text-muted-foreground">
          Conectada por {connectedByName} em {formatDate(installation.created_at)}
        </p>
      </div>
      <Badge variant="outline">
        {installation.account_type === "Organization" ? "Organização" : "Conta pessoal"}
      </Badge>
      {installation.suspended_at && <Badge variant="secondary">Suspensa no GitHub</Badge>}
      <ConfirmActionDialog
        trigger={
          <Button variant="ghost" size="sm" className="text-destructive">
            Desconectar
          </Button>
        }
        title={`Desconectar ${installation.account_login}?`}
        description="O FlowDesk deixa de usar esta conta do GitHub neste workspace. O app continua instalado no GitHub; para removê-lo, desinstale-o nas configurações da conta ou organização lá."
        confirmLabel="Desconectar"
        destructive
        isPending={disconnect.isPending}
        onConfirm={() => disconnect.mutate(installation.id)}
      />
    </div>
  );
}

export function GitHubIntegrationSettings({
  workspaceId,
  workspaceSlug,
}: {
  workspaceId: string;
  workspaceSlug: string;
}) {
  const { data, isLoading, isError, refetch } = useGitHubIntegration(workspaceId);
  const { data: members } = useWorkspaceMembers(workspaceId);
  const connect = useConnectGitHub(workspaceId, workspaceSlug);

  const memberName = (userId: string) =>
    members?.find((member) => member.user.id === userId)?.user.name ?? "um ex-membro";

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="font-heading text-lg font-semibold tracking-tight">GitHub</h2>
          <p className="text-sm text-t2">
            Contas e organizações do GitHub conectadas a este workspace.
          </p>
        </div>
        {data?.configured && (
          <Button disabled={connect.isPending} onClick={() => connect.mutate()}>
            <GitHubIcon className="size-4" />
            Conectar GitHub
          </Button>
        )}
      </div>

      {isLoading ? (
        <ListSkeleton rows={2} />
      ) : isError || !data ? (
        <ErrorState
          message="Não foi possível carregar a integração com o GitHub."
          onRetry={() => refetch()}
        />
      ) : !data.configured ? (
        <EmptyState
          icon={Plug}
          title="Integração indisponível"
          description="O GitHub App não está configurado neste servidor do FlowDesk."
        />
      ) : data.installations.length === 0 ? (
        <EmptyState
          icon={Plug}
          title="Nenhuma conta conectada"
          description="Conecte uma organização ou conta pessoal do GitHub a este workspace."
        />
      ) : (
        <>
          <div className="rounded-xl border border-border bg-panel px-4">
            {data.installations.map((installation) => (
              <InstallationRow
                key={installation.id}
                installation={installation}
                connectedByName={memberName(installation.connected_by_id)}
                workspaceId={workspaceId}
              />
            ))}
          </div>
          <GitHubAutomationRules workspaceId={workspaceId} />
        </>
      )}
    </div>
  );
}
