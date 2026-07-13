# Features

Pasta vazia de propósito na Sprint 1 (Fundação). A partir da Sprint 2, cada feature de domínio
(`auth/`, `workspaces/`, `issues/`, ...) ganha aqui sua própria pasta com `components/`, `hooks/`,
`api.ts` e `types.ts`, seguindo o padrão descrito em `docs/05-frontend.md` §1.

Uma feature só importa de outra feature através do seu `index.ts` (barrel export) — nunca um
import profundo de dentro de `components/` ou `hooks/` de outra feature.
