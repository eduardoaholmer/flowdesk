import { http, HttpResponse } from "msw";

import { API_BASE_URL } from "../apiBaseUrl";
import { demoWorkflowState } from "../fixtures";

export const workflowStatesHandlers = [
  http.get(`${API_BASE_URL}/workspaces/:workspaceId/workflow-states`, () => {
    return HttpResponse.json({ data: [demoWorkflowState] });
  }),
];
