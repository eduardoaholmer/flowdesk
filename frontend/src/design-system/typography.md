# Typography

Fonte de verdade: `src/shared/theme/tokens/typography.ts` (`typographyScale`) e
`src/shared/theme/tokens/fonts.ts` (`fontTokens`).

## Famílias de fonte

Uma única fonte variável (Geist Variable, `@fontsource-variable/geist`) para as duas
categorias semânticas:

```css
--font-sans: "Geist Variable", sans-serif; /* corpo de texto */
--font-heading: "Geist Variable", sans-serif; /* títulos — mesma fonte hoje, nomes
                                                  diferentes para o dia em que a marca
                                                  definitiva trouxer uma display font */
```

`font-heading` já é usado em `CardTitle` (`ui/card.tsx`) e em `PageHeader`
(`shared/components/typography/`) — todo `<h1>`/`<h2>` de página/seção deveria usar
`font-heading`, não `font-sans` implícito.

## Escala de tamanho

`text-xs` → `text-4xl` (7 degraus, `typographyScale`) — a escala default do Tailwind,
não uma escala nova. Convenções já estabelecidas no projeto:

| Elemento                                     | Classe                          |
| -------------------------------------------- | ------------------------------- |
| `PageHeader` título                          | `text-lg font-semibold`         |
| `SectionHeader` título                       | `text-sm font-medium`           |
| Corpo/descrição                              | `text-sm text-muted-foreground` |
| `StatCard` valor                             | `text-2xl font-semibold`        |
| 404/erro de página inteira (`NotFoundState`) | `text-4xl font-semibold`        |

Nenhum tamanho de fonte deveria ser escolhido fora desta escala — se nenhum degrau
serve, isso é sinal de que o layout precisa de ajuste, não de um valor arbitrário
novo.
