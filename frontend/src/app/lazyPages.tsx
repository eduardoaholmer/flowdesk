import { lazy } from "react";

export const IssuesPage = lazy(() =>
  import("@/pages/IssuesPage").then((module) => ({ default: module.IssuesPage })),
);
export const IssueDetailPage = lazy(() =>
  import("@/pages/IssueDetailPage").then((module) => ({ default: module.IssueDetailPage })),
);
export const ProjectsPage = lazy(() =>
  import("@/pages/ProjectsPage").then((module) => ({ default: module.ProjectsPage })),
);
export const ProjectDetailPage = lazy(() =>
  import("@/pages/ProjectDetailPage").then((module) => ({ default: module.ProjectDetailPage })),
);
export const LabelsPage = lazy(() =>
  import("@/pages/LabelsPage").then((module) => ({ default: module.LabelsPage })),
);
export const WorkspaceSettingsPage = lazy(() =>
  import("@/pages/WorkspaceSettingsPage").then((module) => ({
    default: module.WorkspaceSettingsPage,
  })),
);
export const InvitationAcceptPage = lazy(() =>
  import("@/pages/InvitationAcceptPage").then((module) => ({
    default: module.InvitationAcceptPage,
  })),
);
