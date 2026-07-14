/**
 * Espelha o envelope de resposta padrão do backend (CLAUDE.md §8) — todo
 * `httpClient.get/post/patch/delete` tipa sua resposta com um destes.
 */
export interface DataEnvelope<T> {
  data: T;
}

export interface PaginationMeta {
  page: number;
  per_page: number;
  total: number;
  total_pages: number;
}

export interface CollectionEnvelope<T> {
  data: T[];
  meta: PaginationMeta;
}

export interface ApiErrorBody {
  error: {
    code: string;
    message: string;
    details: unknown;
  };
}
