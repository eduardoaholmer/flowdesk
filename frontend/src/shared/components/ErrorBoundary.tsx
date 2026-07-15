import { Component, type ErrorInfo, type ReactNode } from "react";

import { ErrorState } from "@/shared/components/feedback/ErrorState";

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
}

/**
 * React só suporta error boundaries via class component. Cobre erros de
 * render não tratados por nenhuma feature (docs/10-coding-standards.md §9 —
 * nunca tela em branco silenciosa); erros de query/mutation continuam
 * tratados no nível de feature via TanStack Query, não aqui.
 */
export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false };

  static getDerivedStateFromError(): State {
    return { hasError: true };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("Erro não tratado na árvore de componentes.", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex h-screen items-center justify-center p-4">
          <ErrorState
            message="Algo deu errado. Tente recarregar a página."
            onRetry={() => this.setState({ hasError: false })}
          />
        </div>
      );
    }

    return this.props.children;
  }
}
