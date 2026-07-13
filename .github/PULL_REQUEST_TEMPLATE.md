## Descrição

<!-- O que esta PR muda e por quê. -->

## Tipo de mudança

- [ ] `feat` — nova funcionalidade
- [ ] `fix` — correção de bug
- [ ] `refactor` — mudança de código sem alterar comportamento
- [ ] `docs` — apenas documentação
- [ ] `chore` / `build` / `ci` — infraestrutura, dependências, pipeline

## Checklist (CLAUDE.md §18)

- [ ] O código segue o fluxo de camadas (`router → service → repository → model`), sem pular etapas.
- [ ] Toda query com escopo de tenant recebe e aplica `workspace_id` explicitamente.
- [ ] Autorização (RBAC) é checada via `Depends(require_permission(...))`, não com `if` solto.
- [ ] Exceções lançadas são de domínio (`FlowDeskError` e subclasses), não `HTTPException` direto no service.
- [ ] Resposta segue o envelope padrão (`data`/`meta`/`error`) e usa `response_model` explícito.
- [ ] Testes cobrindo o caminho feliz e ao menos um caminho de erro relevante foram escritos e passam.
- [ ] Lint, format e type-check (`ruff`, `mypy` / `eslint`, `tsc`) rodam sem erro.
- [ ] Nenhum segredo, token completo ou dado sensível está sendo logado.
- [ ] `docs/04-api-design.md` e/ou `docs/03-database.md` foram atualizados se o contrato ou o schema mudou.
- [ ] O commit segue Conventional Commits e está no escopo mínimo necessário.

## Como testar

<!-- Passos para validar manualmente esta mudança, se aplicável. -->
