# Forms

Stack: React Hook Form + Zod (ADR-004, `docs/09-decision-log.md`) — nenhum formulário
novo deveria usar `useState` solto para campos quando RHF já resolve isso.

## Campo individual

`ui/field.tsx` já cobre a composição padrão de um campo — não reimplemente label/
descrição/erro manualmente:

```tsx
<Field>
  <FieldLabel htmlFor="email">E-mail</FieldLabel>
  <Input id="email" {...register("email")} aria-invalid={!!errors.email} />
  <FieldDescription>Usamos isto só para login.</FieldDescription>
  <FieldError errors={[errors.email]} />
</Field>
```

`FieldDescription` (texto auxiliar) e `FieldError` (`role="alert"`, erro) já
resolvem o "HelperText dentro de formulário". `HelperText`
(`shared/components/typography/`) é para o caso **fora** de um formulário — não
duplica isto, complementa.

## Busca e filtro (fora de um formulário RHF)

- `SearchInput` (`shared/components/forms/`) — ícone + input + limpar, sobre
  `ui/input-group.tsx`. Substitui o padrão hoje duplicado como `relative`+ícone-
  absoluto em `IssuesToolbar`/`ProjectsToolbar` (não migrados nesta sprint — ver
  ADR-017 — mas disponíveis para a Sprint 9 adotar).
- `FilterBar` (`shared/components/forms/`) — casca responsiva (busca + filtros +
  ação), generaliza o layout já usado por `IssuesToolbar`/`ProjectsToolbar`. Só
  layout: cada feature continua dona do próprio estado/filtro.

## Diálogo de confirmação/exclusão

Não é um formulário RHF — `ConfirmActionDialog`/`DeleteDialog`
(`shared/components/overlay/`), ver `dialogs.md`.
