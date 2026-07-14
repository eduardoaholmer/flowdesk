import { useState } from "react";

/**
 * Sem `useRef`: o lint deste projeto (`react-hooks/refs`, voltado a
 * compatibilidade com o React Compiler) proíbe ler `ref.current` durante o
 * render. Usa o padrão oficial de "ajustar estado durante o render" —
 * https://react.dev/reference/react/useState#storing-information-from-previous-renders
 * — que não lê ref nenhuma e não gera um render extra visível.
 */
export function usePrevious<T>(value: T): T | undefined {
  const [state, setState] = useState<{ value: T; previous: T | undefined }>({
    value,
    previous: undefined,
  });

  if (state.value !== value) {
    setState({ value, previous: state.value });
  }

  return state.previous;
}
