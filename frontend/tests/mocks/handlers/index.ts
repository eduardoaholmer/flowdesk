import { authHandlers } from "./auth";
import { issuesHandlers } from "./issues";
import { notificationsHandlers } from "./notifications";
import { permissionOverridesHandlers } from "./permissionOverrides";
import { projectsHandlers } from "./projects";
import { workflowStatesHandlers } from "./workflowStates";
import { workspacesHandlers } from "./workspaces";

export const handlers = [
  ...authHandlers,
  ...projectsHandlers,
  ...issuesHandlers,
  ...notificationsHandlers,
  ...workflowStatesHandlers,
  ...permissionOverridesHandlers,
  ...workspacesHandlers,
];
