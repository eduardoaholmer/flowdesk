import { createBrowserRouter } from "react-router-dom";

import { AppLayout } from "@/shared/components/layout/AppLayout";
import { RequireAuth } from "@/shared/components/RequireAuth";
import { HomePage } from "@/pages/HomePage";
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
        ],
      },
    ],
  },
  { path: "*", element: <NotFoundPage /> },
]);
