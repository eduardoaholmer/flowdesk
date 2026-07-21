/** Usado por atalhos de teclado sem modificador (ex.: "C" para Nova issue) para não
 * interceptar a tecla sendo digitada num campo de formulário/busca. */
export function isTypingTarget(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false;
  const tag = target.tagName;
  return (
    tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT" || target.contentEditable === "true"
  );
}
