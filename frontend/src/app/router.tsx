import { createBrowserRouter } from "react-router-dom";

import { AppLayout } from "@/shared/components/layout/AppLayout";
import { RequireAuth } from "@/shared/components/RequireAuth";
import { HomePage } from "@/pages/HomePage";
import { IssueDetailPage } from "@/pages/IssueDetailPage";
import { IssuesPage } from "@/pages/IssuesPage";
import { LabelsPage } from "@/pages/LabelsPage";
import { LoginPage } from "@/pages/LoginPage";
import { NotFoundPage } from "@/pages/NotFoundPage";
import { ProjectDetailPage } from "@/pages/ProjectDetailPage";
import { ProjectsPage } from "@/pages/ProjectsPage";

export const router = createBrowserRouter([
  { path: "/login", element: <LoginPage /> },
  {
    element: <RequireAuth />,
    children: [
      {
        element: <AppLayout />,
        children: [
          { index: true, path: "/", element: <HomePage /> },
          { path: "/w/:workspaceSlug/projects", element: <ProjectsPage /> },
          { path: "/w/:workspaceSlug/projects/:projectId", element: <ProjectDetailPage /> },
          { path: "/w/:workspaceSlug/issues", element: <IssuesPage /> },
          { path: "/w/:workspaceSlug/issues/:issueId", element: <IssueDetailPage /> },
          { path: "/w/:workspaceSlug/labels", element: <LabelsPage /> },
        ],
      },
    ],
  },
  { path: "*", element: <NotFoundPage /> },
]);
