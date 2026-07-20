import { useMemo, useState } from "react";

import { Input } from "@/shared/components/ui/input";
import { Popover, PopoverContent, PopoverTrigger } from "@/shared/components/ui/popover";
import { ScrollArea } from "@/shared/components/ui/scroll-area";
import { cn } from "@/shared/lib/utils";

interface EmojiEntry {
  emoji: string;
  keywords: string;
}

const EMOJI_ENTRIES: EmojiEntry[] = [
  { emoji: "🚀", keywords: "foguete lançamento rocket" },
  { emoji: "🎯", keywords: "alvo meta objetivo target" },
  { emoji: "📦", keywords: "pacote box entrega release" },
  { emoji: "🛠️", keywords: "ferramenta tools build" },
  { emoji: "⚙️", keywords: "engrenagem config gear" },
  { emoji: "🧩", keywords: "peça puzzle integração" },
  { emoji: "📊", keywords: "gráfico chart dados analytics" },
  { emoji: "📈", keywords: "crescimento growth chart" },
  { emoji: "📁", keywords: "pasta folder arquivo" },
  { emoji: "🗂️", keywords: "pasta organização arquivo" },
  { emoji: "📝", keywords: "nota anotação doc" },
  { emoji: "📋", keywords: "checklist prancheta board" },
  { emoji: "✅", keywords: "check concluído done" },
  { emoji: "🔥", keywords: "fogo urgente hot" },
  { emoji: "⚡", keywords: "raio rápido fast" },
  { emoji: "💡", keywords: "ideia lâmpada insight" },
  { emoji: "🐛", keywords: "bug inseto erro" },
  { emoji: "🔧", keywords: "chave ferramenta fix" },
  { emoji: "🔩", keywords: "parafuso peça" },
  { emoji: "🧪", keywords: "teste experimento lab" },
  { emoji: "🔬", keywords: "pesquisa microscópio" },
  { emoji: "🧠", keywords: "cérebro ideia inteligência" },
  { emoji: "🖥️", keywords: "computador desktop sistema" },
  { emoji: "💻", keywords: "laptop notebook código" },
  { emoji: "📱", keywords: "celular mobile app" },
  { emoji: "🌐", keywords: "globo web internet" },
  { emoji: "☁️", keywords: "nuvem cloud" },
  { emoji: "🔒", keywords: "cadeado segurança lock" },
  { emoji: "🔑", keywords: "chave acesso key" },
  { emoji: "🛡️", keywords: "escudo segurança shield" },
  { emoji: "💰", keywords: "dinheiro financeiro money" },
  { emoji: "💳", keywords: "cartão pagamento payment" },
  { emoji: "🛒", keywords: "carrinho compra shop" },
  { emoji: "📣", keywords: "anúncio marketing megafone" },
  { emoji: "📢", keywords: "anúncio comunicação" },
  { emoji: "🎨", keywords: "design arte paleta" },
  { emoji: "🖌️", keywords: "design pincel arte" },
  { emoji: "✏️", keywords: "editar lápis draft" },
  { emoji: "📐", keywords: "régua design layout" },
  { emoji: "🧭", keywords: "bússola direção roadmap" },
  { emoji: "🗺️", keywords: "mapa roadmap plano" },
  { emoji: "🏁", keywords: "bandeira meta finish" },
  { emoji: "🚩", keywords: "bandeira marco milestone" },
  { emoji: "⭐", keywords: "estrela destaque favorito" },
  { emoji: "🌟", keywords: "estrela brilho destaque" },
  { emoji: "🏆", keywords: "troféu conquista prêmio" },
  { emoji: "🎉", keywords: "festa celebração launch" },
  { emoji: "📅", keywords: "calendário data agenda" },
  { emoji: "⏰", keywords: "relógio prazo tempo" },
  { emoji: "⏳", keywords: "ampulheta prazo tempo" },
  { emoji: "👥", keywords: "pessoas time equipe team" },
  { emoji: "🤝", keywords: "aperto de mão parceria" },
  { emoji: "💬", keywords: "conversa chat comentário" },
  { emoji: "📨", keywords: "mensagem email envio" },
  { emoji: "🔔", keywords: "sino notificação alerta" },
  { emoji: "🧱", keywords: "tijolo infraestrutura base" },
  { emoji: "🏗️", keywords: "construção infraestrutura" },
  { emoji: "🌱", keywords: "planta crescimento novo" },
  { emoji: "🌳", keywords: "árvore estrutura" },
  { emoji: "🔗", keywords: "link integração conexão" },
  { emoji: "🧲", keywords: "ímã atração" },
  { emoji: "🎲", keywords: "dado jogo aleatório" },
  { emoji: "🕹️", keywords: "jogo game controle" },
  { emoji: "📷", keywords: "câmera foto mídia" },
  { emoji: "🎬", keywords: "filme vídeo produção" },
  { emoji: "🎵", keywords: "música áudio" },
  { emoji: "🧾", keywords: "recibo fatura nota" },
  { emoji: "📉", keywords: "queda gráfico decline" },
  { emoji: "🏢", keywords: "prédio empresa office" },
  { emoji: "🏠", keywords: "casa home início" },
  { emoji: "🌍", keywords: "mundo global internacional" },
  { emoji: "✈️", keywords: "viagem avião travel" },
];

function EmojiButton({
  entry,
  selected,
  onSelect,
}: {
  entry: EmojiEntry;
  selected: boolean;
  onSelect: (emoji: string) => void;
}) {
  return (
    <button
      type="button"
      onClick={() => onSelect(entry.emoji)}
      aria-label={entry.keywords.split(" ")[0]}
      aria-pressed={selected}
      className={cn(
        "flex h-9 w-9 items-center justify-center rounded-md text-lg transition-colors hover:bg-accent",
        selected && "bg-accent ring-1 ring-ring",
      )}
    >
      {entry.emoji}
    </button>
  );
}

export function EmojiIconPicker({
  value,
  onChange,
  id,
  placeholder = "Escolher ícone",
}: {
  value?: string;
  onChange: (emoji: string) => void;
  id?: string;
  placeholder?: string;
}) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");

  const results = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    if (!normalized) return EMOJI_ENTRIES;
    return EMOJI_ENTRIES.filter((entry) => entry.keywords.includes(normalized));
  }, [query]);

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <button
          id={id}
          type="button"
          className="flex h-10 w-full items-center gap-2 rounded-md border border-input bg-transparent px-3 text-sm shadow-xs transition-colors hover:bg-accent/50"
        >
          <span className="flex h-6 w-6 items-center justify-center text-lg">{value || "🙂"}</span>
          <span className={cn("truncate", !value && "text-muted-foreground")}>
            {value ? "Trocar ícone" : placeholder}
          </span>
        </button>
      </PopoverTrigger>
      <PopoverContent className="w-64" align="start">
        <Input
          autoFocus
          placeholder="Buscar ícone…"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
        />
        <ScrollArea className="h-48">
          <div className="grid grid-cols-6 gap-1 p-0.5">
            {results.map((entry) => (
              <EmojiButton
                key={entry.emoji}
                entry={entry}
                selected={entry.emoji === value}
                onSelect={(emoji) => {
                  onChange(emoji);
                  setOpen(false);
                }}
              />
            ))}
            {results.length === 0 && (
              <p className="col-span-6 py-4 text-center text-xs text-muted-foreground">
                Nenhum ícone encontrado.
              </p>
            )}
          </div>
        </ScrollArea>
      </PopoverContent>
    </Popover>
  );
}
