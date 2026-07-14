# Features

Cada feature de domínio (`auth/`, `workspaces/`, `issues/`, `projects/`, `labels/`,
`comments/`, `attachments/`, ...) tem sua própria pasta com `components/`,
`hooks.ts`, `api.ts` e `types.ts`. A convenção real de import entre features —
incluindo o desvio do `index.ts`/barrel originalmente planejado — está
documentada em `docs/05-frontend.md` §1 (nota pós-implementação da Sprint 6/7);
esse documento é a fonte de verdade, não este arquivo.
