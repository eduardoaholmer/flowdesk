import { RouterProvider } from "react-router-dom";

import { AppProviders } from "@/app/providers";
import { AuthBootstrap } from "@/app/AuthBootstrap";
import { router } from "@/app/router";

export function App() {
  return (
    <AppProviders>
      <AuthBootstrap>
        <RouterProvider router={router} />
      </AuthBootstrap>
    </AppProviders>
  );
}
