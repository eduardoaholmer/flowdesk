import { Suspense, type ReactNode } from "react";
import { createBrowserRouter } from "react-router-dom";

import {
  IssueDetailPage,
  IssuesPage,
  LabelsPage,
  ProjectDetailPage,
  ProjectsPage,
} from "@/app/lazyPages";
import { AppLayout } from "@/shared/components/layout/AppLayout";
import { RequireAuth } from "@/shared/components/RequireAuth";
import { PageSkeleton } from "@/shared/components/skeletons/PageSkeleton";
import { routePatterns } from "@/shared/lib/routes";
import { HomePage } from "@/pages/HomePage";
import { LoginPage } from "@/pages/LoginPage";
import { NotFoundPage } from "@/pages/NotFoundPage";

/** HomePage/LoginPage/NotFoundPage ficam fora do lazy — pequenas e sempre necessárias cedo. */
function withPageSuspense(element: ReactNode) {
  return <Suspense fallback={<PageSkeleton />}>{element}</Suspense>;
}

export const router = createBrowserRouter([
  { path: "/login", element: <LoginPage /> },
  {
    element: <RequireAuth />,
    children: [
      {
        element: <AppLayout />,
        children: [
          { index: true, path: "/", element: <HomePage /> },
          { path: routePatterns.projects, element: withPageSuspense(<ProjectsPage />) },
          {
            path: routePatterns.projectDetail,
            element: withPageSuspense(<ProjectDetailPage />),
          },
          { path: routePatterns.issues, element: withPageSuspense(<IssuesPage />) },
          { path: routePatterns.issueDetail, element: withPageSuspense(<IssueDetailPage />) },
          { path: routePatterns.labels, element: withPageSuspense(<LabelsPage />) },
        ],
      },
    ],
  },
  { path: "*", element: <NotFoundPage /> },
]);
