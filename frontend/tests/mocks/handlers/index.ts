import { authHandlers } from "./auth";
import { issuesHandlers } from "./issues";
import { notificationsHandlers } from "./notifications";
import { projectsHandlers } from "./projects";
import { workspacesHandlers } from "./workspaces";

export const handlers = [
  ...authHandlers,
  ...projectsHandlers,
  ...issuesHandlers,
  ...notificationsHandlers,
  ...workspacesHandlers,
];
