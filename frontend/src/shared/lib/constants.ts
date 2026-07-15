/**
 * `per_page` usado quando o objetivo é buscar "todos os itens" para popular um
 * seletor/picker (ex.: lista de projetos no formulário de issue, membros do
 * workspace) — não é paginação de UI real, então não precisa ser grande o
 * bastante para cobrir qualquer workspace, só o suficiente para o caso comum.
 */
export const MAX_PICKER_PAGE_SIZE = 100;
