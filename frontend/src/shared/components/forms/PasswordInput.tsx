import { Eye, EyeOff } from "lucide-react";
import { useState, type ComponentProps } from "react";

import {
  InputGroup,
  InputGroupAddon,
  InputGroupButton,
  InputGroupInput,
} from "@/shared/components/ui/input-group";

/**
 * Campo de senha com alternância de visibilidade (ícone de olho), composto sobre
 * `ui/input-group.tsx` seguindo o mesmo padrão de `SearchInput`. Substitui o
 * `<Input type="password">` cru usado em login/registro/redefinição de senha.
 */
export function PasswordInput({ className, ...props }: Omit<ComponentProps<"input">, "type">) {
  const [isVisible, setIsVisible] = useState(false);

  return (
    <InputGroup className={className}>
      <InputGroupInput type={isVisible ? "text" : "password"} {...props} />
      <InputGroupAddon align="inline-end">
        <InputGroupButton
          type="button"
          aria-label={isVisible ? "Ocultar senha" : "Mostrar senha"}
          size="icon-xs"
          onClick={() => setIsVisible((visible) => !visible)}
        >
          {isVisible ? <EyeOff /> : <Eye />}
        </InputGroupButton>
      </InputGroupAddon>
    </InputGroup>
  );
}
