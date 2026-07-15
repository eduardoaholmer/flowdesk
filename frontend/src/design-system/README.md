# FlowDesk Product Design System

Documentação interna para quem constrói UI neste projeto — não um produto documentado
para usuário final. Escrita na Sprint 8.5 (`docs/08-roadmap.md`), antes da identidade
visual definitiva existir: **toda cor aqui é placeholder** (grayscale, `src/index.css`)
e o objetivo explícito é que trocar a marca real só troque valores de cor, nunca a
estrutura documentada abaixo. A marca real (`brand/Logo.tsx`, "Ring Gate") já foi
integrada como o primeiro caso concreto disso — só trocou a cor de tinta usada pela
marca, não a estrutura de componentes.

## Como isto se relaciona com o resto do repositório

- **Fonte de verdade dos valores**: `src/shared/theme/tokens/*.ts` (um arquivo por
  categoria — sem barrel, ver `docs/05-frontend.md` §1) e `src/index.css` (CSS custom
  properties). Este diretório documenta o _padrão de uso_, não redefine valor nenhum.
- **Componentes**: `src/shared/components/ui/` são as primitivas shadcn/ui (não
  editar convenção à mão — CLAUDE.md §17); `src/shared/components/{layout,
navigation, typography, data-display, forms, overlay, feedback, motion, brand}/`
  são os componentes compostos reutilizáveis construídos sobre elas (Sprint 8.5).
  Boa parte deles ainda não tem um call site em uma tela final — são a fundação
  preparada por esta sprint para que a sprint de identidade visual/telas finais não
  precise de refatoração estrutural (objetivo explícito da Sprint 8.5,
  `docs/08-roadmap.md`); adotar cada um em uma tela real é trabalho de sprint futura,
  não desta.
- **Storybook**: cogitado como base interativa complementar a estes documentos, ainda
  sem sprint atribuída no roadmap — não existe `.storybook/` neste repositório hoje.

## Índice

- [Spacing](./spacing.md)
- [Typography](./typography.md)
- [Radius](./radius.md)
- [Shadow](./shadow.md)
- [Elevation](./elevation.md)
- [Motion](./motion.md)
- [Icons](./icons.md)
- [Forms](./forms.md)
- [Buttons](./buttons.md)
- [Cards](./cards.md)
- [Tables](./tables.md)

**Sem doc dedicada ainda** (categoria existe como componente, mas não foi documentada
neste índice — trabalho futuro, não desta sprint): Kanban (feature ainda não existe),
Dialogs, Dropdowns, Badges, Empty/Error/Loading States.
