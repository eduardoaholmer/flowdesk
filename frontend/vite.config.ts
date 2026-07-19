/// <reference types="vitest/config" />
import path from "node:path";

import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    host: true,
    port: 5173,
  },
  test: {
    environment: "jsdom",
    setupFiles: ["./tests/setup.ts"],
    // `exclude` explícito substitui o default do Vitest inteiro (não soma) — por
    // isso repete os defaults (node_modules/dist/.git/configs) e acrescenta `e2e/`,
    // que tem specs do Playwright (`*.spec.ts`) que o Vitest tentaria rodar sozinho.
    exclude: [
      "**/node_modules/**",
      "**/dist/**",
      "**/e2e/**",
      "**/.{idea,git,cache,output,temp}/**",
      "**/{karma,rollup,webpack,vite,vitest,jest,ava,babel,nyc,cjs,mocha,eslint,prettier}.config.*",
    ],
  },
});
