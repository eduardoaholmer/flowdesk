# Typography

Fonte de verdade: `src/shared/theme/tokens/typography.ts` (`typographyScale`) e
`src/shared/theme/tokens/fonts.ts` (`fontTokens`).

## Famílias de fonte

Duas fontes variáveis, cada uma self-hosted via `@fontsource-variable/*` (sem
requisição a CDN de terceiro, mesmo padrão para as duas):

```css
--font-sans: "Geist Variable", sans-serif; /* corpo de texto */
--font-heading: "Fraunces Variable", serif; /* títulos — serif de exibição,
                                                combina com a rampa de neutros
                                                quentes derivada de --brand-ink/
                                                --brand-paper (ADR-019); ver
                                                ADR-024 para o racional completo
                                                da escolha */
```

`font-heading` já é usado em `CardTitle` (`ui/card.tsx`), `PageHeader`
(`shared/components/typography/`), `StatCard`, e nos títulos de `Dialog`/
`AlertDialog`/`Sheet`/`Empty` — todo `<h1>`/`<h2>` de página/seção deveria usar
`font-heading`, não `font-sans` implícito. Fraunces expõe um eixo de peso
variável completo (100–900), então `font-medium`/`font-semibold` já em uso em
todos esses consumidores funcionam sem ajuste por componente.

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
