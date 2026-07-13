# Contribuindo com o FlowDesk

FlowDesk é um projeto de portfólio, mas segue o mesmo processo que se esperaria de um
repositório mantido em produção. Este guia resume como propor mudanças; as regras completas
de engenharia (arquitetura, padrões de código, testes) estão em [`CLAUDE.md`](./CLAUDE.md) e
na pasta [`docs/`](./docs).

## Antes de começar

1. Leia [`CLAUDE.md`](./CLAUDE.md) — é a fonte de verdade de como o projeto é construído.
   Qualquer mudança de código deve obedecer ao fluxo de camadas, padrões de nomenclatura e
   estratégia de testes descritos lá.
2. Para mudanças de escopo maior, abra uma issue antes de escrever código, descrevendo o
   problema e a abordagem proposta.

## Ambiente local

Veja a seção "Como executar localmente" no [`README.md`](./README.md) — via Docker Compose ou
rodando backend/frontend manualmente.

## Fluxo de contribuição

1. Crie um branch a partir de `main` (`feat/<escopo>`, `fix/<escopo>`, `chore/<escopo>`...).
2. Garanta que lint, type-check e testes passam localmente antes de abrir a PR (comandos na
   seção "Qualidade e testes" do README).
3. Commits seguem [Conventional Commits](https://www.conventionalcommits.org/), conforme
   `CLAUDE.md` §15 — tipos permitidos: `feat`, `fix`, `refactor`, `perf`, `test`, `docs`,
   `chore`, `build`, `ci`. Um commit = uma mudança logicamente coesa.
4. Abra a PR preenchendo o template — ele espelha o checklist de conformidade de `CLAUDE.md`
   §18 (camadas, isolamento de tenant, RBAC, testes, lint).
5. CI (`.github/workflows/ci.yml`) precisa passar antes do merge.

## Mudança de contrato de API ou schema de banco

Se a mudança altera o contrato documentado em `docs/04-api-design.md` ou o modelo de dados em
`docs/03-database.md`, esses documentos devem ser atualizados no mesmo PR. Decisões
arquiteturais novas (nova dependência, mudança de padrão) exigem uma entrada em
`docs/09-decision-log.md`.
