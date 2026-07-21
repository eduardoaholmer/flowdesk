# Tables

Primitivo: `ui/table.tsx` — usado hoje por `IssuesTable`/`LabelsTable`
(`features/*/components/`), cada um dono do próprio conjunto de colunas
(tabelas são específicas de domínio, não um componente genérico de "tabela
de qualquer coisa"). Projetos deixou de usar tabela na Sprint 19.2 — vira um
grid de cards (`ProjectsGrid`/`ProjectCard`), mais próximo do handoff de M7
(`Projetos e Labels.dc.html`) do que uma listagem tabular.

## Padrão de listagem já estabelecido (issues/labels)

```
FilterBar (busca + filtros + ação "criar")
  ↓
ListSkeleton (loading) | ErrorState (erro) | <Feature>Table + Pagination (dado) | EmptyState (vazio)
```

Ver `shared/components/skeletons/ListSkeleton.tsx`, `shared/components/feedback/
{ErrorState,EmptyState}.tsx`, `shared/components/navigation/Pagination.tsx` —
`Pagination` é genérico (`meta`, `itemLabel`, `onPageChange`), consolidado nesta
sprint a partir de `IssuesPagination`/`ProjectsPagination` (que eram idênticos byte a
byte, ver ADR-017).

## `TableSkeleton`

`shared/components/skeletons/TableSkeleton.tsx` já existe (`columns`, `rows`) mas
ainda não tem consumidor real — `ListSkeleton` (linhas soltas) é o que
Issues/Labels usam hoje porque a tabela em si tem poucas colunas visíveis.
Projetos usa `CardSkeleton` (Sprint 19.2), repetido no mesmo grid do estado
carregado — mais fiel ao layout de card do que linhas soltas. Uma tabela
futura com cabeçalho de coluna visível e mais densidade (ex.: uma tela de
relatório na Sprint 9) é o caso que justifica trocar para `TableSkeleton`.
