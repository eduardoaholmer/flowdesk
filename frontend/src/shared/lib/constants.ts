/**
 * `per_page` usado quando o objetivo é buscar "todos os itens" para popular um
 * seletor/picker (ex.: lista de projetos no formulário de issue, membros do
 * workspace) — não é paginação de UI real, então não precisa ser grande o
 * bastante para cobrir qualquer workspace, só o suficiente para o caso comum.
 */
export const MAX_PICKER_PAGE_SIZE = 100;

/**
 * Faixa de negócio para `Issue.due_date`, espelhando a validação do backend
 * (`backend/src/features/issues/schemas.py::_validate_due_date`) — evita que
 * um erro de digitação (ex.: ano "0002") seja aceito pelo `<input type=date>`.
 */
export const DUE_DATE_MIN = "1900-01-01";
export const DUE_DATE_MAX = "2200-12-31";
