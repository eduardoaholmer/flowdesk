import { RouterProvider } from "react-router-dom";

import { AppProviders } from "@/app/providers";
import { AuthBootstrap } from "@/app/AuthBootstrap";
import { router } from "@/app/router";
import { ErrorBoundary } from "@/shared/components/ErrorBoundary";

export function App() {
  return (
    <ErrorBoundary>
      <AppProviders>
        <AuthBootstrap>
          <RouterProvider router={router} />
        </AuthBootstrap>
      </AppProviders>
    </ErrorBoundary>
  );
}
