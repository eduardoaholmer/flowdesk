import { useSearchParams } from "react-router-dom";

import { GitHubIntegrationSettings } from "@/features/github/components/GitHubIntegrationSettings";
import { WorkflowStatesSettings } from "@/features/workflow-states/components/WorkflowStatesSettings";
import { PermissionsSettings } from "@/features/permissions/components/PermissionsSettings";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/shared/components/ui/tabs";

import type { WorkspaceRole } from "../types";
import { WorkspaceGeneralSettings } from "./WorkspaceGeneralSettings";
import { WorkspaceInvitationsSettings } from "./WorkspaceInvitationsSettings";
import { WorkspaceMembersSettings } from "./WorkspaceMembersSettings";

export function WorkspaceSettingsPage({
  workspaceId,
  workspaceSlug,
  role,
}: {
  workspaceId: string;
  workspaceSlug: string;
  role: WorkspaceRole;
}) {
  const canManage = role === "OWNER" || role === "ADMIN";
  const isOwner = role === "OWNER";
  const [searchParams] = useSearchParams();
  // `?tab=integrations` é o destino da volta do GitHub (`GitHubCallbackPage`).
  const initialTab =
    searchParams.get("tab") === "integrations" && canManage ? "integrations" : "general";

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="font-heading text-xl font-semibold tracking-tight">
          Configurações do workspace
        </h1>
        <p className="text-sm text-t2">Nome, membros, convites e integrações deste workspace.</p>
      </div>

      <Tabs defaultValue={initialTab}>
        {/* Seis abas não cabem em 390px: a lista rola na horizontal em vez de
            cortar a última aba ou alargar a página. */}
        <TabsList className="max-w-full justify-start overflow-x-auto">
          <TabsTrigger value="general">Geral</TabsTrigger>
          <TabsTrigger value="members">Membros</TabsTrigger>
          {canManage && <TabsTrigger value="invitations">Convites</TabsTrigger>}
          {canManage && <TabsTrigger value="workflow-states">Status</TabsTrigger>}
          {isOwner && <TabsTrigger value="permissions">Permissões</TabsTrigger>}
          {canManage && <TabsTrigger value="integrations">Integrações</TabsTrigger>}
        </TabsList>
        <TabsContent value="general" className="pt-4">
          <WorkspaceGeneralSettings
            workspaceId={workspaceId}
            canEdit={canManage}
            canDelete={isOwner}
          />
        </TabsContent>
        <TabsContent value="members" className="pt-4">
          <WorkspaceMembersSettings
            workspaceId={workspaceId}
            canManage={canManage}
            isOwner={isOwner}
          />
        </TabsContent>
        {canManage && (
          <TabsContent value="invitations" className="pt-4">
            <WorkspaceInvitationsSettings workspaceId={workspaceId} />
          </TabsContent>
        )}
        {canManage && (
          <TabsContent value="workflow-states" className="pt-4">
            <WorkflowStatesSettings workspaceId={workspaceId} />
          </TabsContent>
        )}
        {isOwner && (
          <TabsContent value="permissions" className="pt-4">
            <PermissionsSettings workspaceId={workspaceId} />
          </TabsContent>
        )}
        {canManage && (
          <TabsContent value="integrations" className="pt-4">
            <GitHubIntegrationSettings workspaceId={workspaceId} workspaceSlug={workspaceSlug} />
          </TabsContent>
        )}
      </Tabs>
    </div>
  );
}
