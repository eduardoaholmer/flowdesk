import { HexColorInput, HexColorPicker } from "react-colorful";
import { useState } from "react";

import { Popover, PopoverContent, PopoverTrigger } from "@/shared/components/ui/popover";
import { cn } from "@/shared/lib/utils";

const PRESET_COLORS = [
  "#EF4444",
  "#F97316",
  "#F59E0B",
  "#EAB308",
  "#84CC16",
  "#22C55E",
  "#10B981",
  "#14B8A6",
  "#06B6D4",
  "#0EA5E9",
  "#3B82F6",
  "#4F46E5",
  "#8B5CF6",
  "#A855F7",
  "#D946EF",
  "#EC4899",
  "#F43F5E",
  "#64748B",
];

const DEFAULT_COLOR = "#4F46E5";

function isValidHex(value: string) {
  return /^#(?:[0-9A-Fa-f]{3}|[0-9A-Fa-f]{6})$/.test(value);
}

export function ColorSwatchPicker({
  value,
  onChange,
  id,
  placeholder = "Escolher cor",
}: {
  value?: string;
  onChange: (color: string) => void;
  id?: string;
  placeholder?: string;
}) {
  const [open, setOpen] = useState(false);
  const color = value && isValidHex(value) ? value : DEFAULT_COLOR;

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <button
          id={id}
          type="button"
          className="flex h-10 w-full items-center gap-2 rounded-md border border-input bg-transparent px-3 text-sm shadow-xs transition-colors hover:bg-accent/50"
        >
          <span
            className="h-5 w-5 shrink-0 rounded-full ring-1 ring-foreground/10"
            style={{ backgroundColor: color }}
          />
          <span className={cn("truncate", !value && "text-muted-foreground")}>
            {value || placeholder}
          </span>
        </button>
      </PopoverTrigger>
      <PopoverContent className="w-64" align="start">
        <HexColorPicker color={color} onChange={onChange} className="!w-full" />

        <div className="grid grid-cols-9 gap-1.5">
          {PRESET_COLORS.map((preset) => (
            <button
              key={preset}
              type="button"
              aria-label={preset}
              onClick={() => onChange(preset)}
              className={cn(
                "h-5 w-5 rounded-full ring-1 ring-foreground/10 transition-transform hover:scale-110",
                preset.toLowerCase() === color.toLowerCase() &&
                  "ring-2 ring-ring ring-offset-1 ring-offset-popover",
              )}
              style={{ backgroundColor: preset }}
            />
          ))}
        </div>

        <div className="flex items-center gap-2 rounded-md border border-input px-2.5 focus-within:ring-1 focus-within:ring-ring">
          <span className="text-sm text-muted-foreground">#</span>
          <HexColorInput
            color={color}
            onChange={onChange}
            prefixed={false}
            className="h-8 w-full bg-transparent text-sm uppercase outline-hidden"
          />
        </div>
      </PopoverContent>
    </Popover>
  );
}
