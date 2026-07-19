import { http, HttpResponse } from "msw";

import { API_BASE_URL } from "../apiBaseUrl";
import { demoUser } from "../fixtures";

export const authHandlers = [
  http.post(`${API_BASE_URL}/auth/login`, async ({ request }) => {
    const body = (await request.json()) as { email: string };
    return HttpResponse.json({
      data: {
        access_token: "mock-access-token",
        user: { ...demoUser, email: body.email },
      },
    });
  }),

  http.post(`${API_BASE_URL}/auth/register`, async ({ request }) => {
    const body = (await request.json()) as { name: string; email: string };
    return HttpResponse.json(
      { data: { ...demoUser, name: body.name, email: body.email } },
      { status: 201 },
    );
  }),

  http.post(`${API_BASE_URL}/auth/logout`, () => new HttpResponse(null, { status: 204 })),

  http.post(
    `${API_BASE_URL}/auth/password-reset/request`,
    () => new HttpResponse(null, { status: 204 }),
  ),

  http.post(
    `${API_BASE_URL}/auth/password-reset/confirm`,
    () => new HttpResponse(null, { status: 204 }),
  ),
];
