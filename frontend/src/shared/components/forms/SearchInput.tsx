import { Search, X } from "lucide-react";

import {
  InputGroup,
  InputGroupAddon,
  InputGroupButton,
  InputGroupInput,
} from "@/shared/components/ui/input-group";

interface SearchInputProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  className?: string;
}

/**
 * Composição padrão de busca (ícone + input + limpar) sobre `ui/input-group.tsx` —
 * substitui o padrão hoje duplicado como `relative`/ícone-absoluto em
 * `IssuesToolbar`/`ProjectsToolbar` (não migrados nesta sprint — ver plano da
 * Sprint 8.8/8.9 — mas disponível para a Sprint 9 usar desde já).
 */
export function SearchInput({ value, onChange, placeholder, className }: SearchInputProps) {
  return (
    <InputGroup className={className}>
      <InputGroupAddon>
        <Search />
      </InputGroupAddon>
      <InputGroupInput
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder ?? "Buscar…"}
      />
      {value && (
        <InputGroupAddon align="inline-end">
          <InputGroupButton
            type="button"
            aria-label="Limpar busca"
            size="icon-xs"
            onClick={() => onChange("")}
          >
            <X />
          </InputGroupButton>
        </InputGroupAddon>
      )}
    </InputGroup>
  );
}
