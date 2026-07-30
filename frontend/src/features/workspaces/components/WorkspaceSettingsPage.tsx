import { WorkflowStatesSettings } from "@/features/workflow-states/components/WorkflowStatesSettings";
import { PermissionsSettings } from "@/features/permissions/components/PermissionsSettings";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/shared/components/ui/tabs";

import type { WorkspaceRole } from "../types";
import { WorkspaceGeneralSettings } from "./WorkspaceGeneralSettings";
import { WorkspaceInvitationsSettings } from "./WorkspaceInvitationsSettings";
import { WorkspaceMembersSettings } from "./WorkspaceMembersSettings";

export function WorkspaceSettingsPage({
  workspaceId,
  role,
}: {
  workspaceId: string;
  role: WorkspaceRole;
}) {
  const canManage = role === "OWNER" || role === "ADMIN";
  const isOwner = role === "OWNER";

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="font-heading text-xl font-semibold tracking-tight">
          Configurações do workspace
        </h1>
        <p className="text-sm text-t2">Nome, membros e convites deste workspace.</p>
      </div>

      <Tabs defaultValue="general">
        <TabsList>
          <TabsTrigger value="general">Geral</TabsTrigger>
          <TabsTrigger value="members">Membros</TabsTrigger>
          {canManage && <TabsTrigger value="invitations">Convites</TabsTrigger>}
          {canManage && <TabsTrigger value="workflow-states">Status</TabsTrigger>}
          {isOwner && <TabsTrigger value="permissions">Permissões</TabsTrigger>}
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
      </Tabs>
    </div>
  );
}
