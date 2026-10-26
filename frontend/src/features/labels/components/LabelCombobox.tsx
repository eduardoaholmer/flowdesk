import { Plus } from "lucide-react";
import { useState, type ReactNode } from "react";

import {
  Command,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/shared/components/ui/command";
import { Popover, PopoverContent, PopoverTrigger } from "@/shared/components/ui/popover";
import { PRESET_COLORS } from "@/shared/lib/constants";

import { useCreateLabel, useLabels } from "../hooks";
import type { Label } from "../types";

/**
 * Busca, marca/desmarca e cria labels sem sair da issue — quem decide o que
 * "marcar" significa é quem usa: aplicar na hora (`IssueLabelPicker`, issue já
 * existe) ou só guardar o id no formulário (`CreateIssueDialog`, issue ainda não
 * existe). Uma label criada aqui já volta marcada.
 */
export function LabelCombobox({
  workspaceId,
  selectedIds,
  onToggle,
  children,
}: {
  workspaceId: string;
  selectedIds: ReadonlySet<string>;
  onToggle: (label: Label, selected: boolean) => void;
  children: ReactNode;
}) {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");
  const { data: labels = [] } = useLabels(workspaceId);
  const createLabel = useCreateLabel(workspaceId);

  const term = search.trim();
  const normalizedTerm = term.toLowerCase();
  const visibleLabels = labels.filter((label) => label.name.toLowerCase().includes(normalizedTerm));
  // Case-insensitive de propósito, embora o backend só recuse nome idêntico:
  // oferecer criar "Bug" ao lado de "bug" só geraria duas labels quase iguais.
  const canCreate =
    term.length > 0 && !labels.some((label) => label.name.toLowerCase() === normalizedTerm);

  async function handleCreate() {
    try {
      const created = await createLabel.mutateAsync({
        name: term,
        color: PRESET_COLORS[labels.length % PRESET_COLORS.length] ?? "#4F46E5",
      });
      setSearch("");
      onToggle(created, true);
    } catch {
      // `useCreateLabel` já mostra o erro em toast; o termo fica no campo para corrigir.
    }
  }

  return (
    <Popover
      open={open}
      onOpenChange={(next) => {
        setOpen(next);
        if (!next) setSearch("");
      }}
    >
      <PopoverTrigger asChild>{children}</PopoverTrigger>
      <PopoverContent align="start" className="w-64 p-0">
        <Command shouldFilter={false}>
          <CommandInput
            placeholder="Buscar ou criar label…"
            value={search}
            onValueChange={setSearch}
            maxLength={50}
          />
          <CommandList>
            {visibleLabels.length > 0 && (
              <CommandGroup>
                {visibleLabels.map((label) => {
                  const isSelected = selectedIds.has(label.id);
                  return (
                    <CommandItem
                      key={label.id}
                      value={label.id}
                      data-checked={isSelected}
                      onSelect={() => onToggle(label, !isSelected)}
                    >
                      <span
                        className="inline-block size-2 shrink-0 rounded-full"
                        style={{ backgroundColor: label.color }}
                      />
                      <span className="truncate">{label.name}</span>
                    </CommandItem>
                  );
                })}
              </CommandGroup>
            )}
            {canCreate && (
              <CommandGroup>
                <CommandItem
                  value="__create__"
                  disabled={createLabel.isPending}
                  onSelect={handleCreate}
                >
                  <Plus />
                  <span className="truncate">Criar label “{term}”</span>
                </CommandItem>
              </CommandGroup>
            )}
            {visibleLabels.length === 0 && !canCreate && (
              <p className="px-2 py-6 text-center text-sm text-muted-foreground">
                {labels.length === 0
                  ? "Nenhuma label ainda. Digite um nome para criar."
                  : "Nenhuma label encontrada."}
              </p>
            )}
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  );
}
