import { useCallback } from "react";

import { useLocalStorage } from "@/shared/hooks/useLocalStorage";

export interface RecentCommand {
  id: string;
  label: string;
  to: string;
}

const STORAGE_KEY = "flowdesk:command-palette:recent";
const MAX_RECENT = 5;

/** Só rastreia destinos de navegação (têm `to`) — uma ação pura (tema, logout)
 * não é algo que faça sentido "revisitar". */
export function useRecentCommands() {
  const [recent, setRecent] = useLocalStorage<RecentCommand[]>(STORAGE_KEY, []);

  const addRecent = useCallback(
    (entry: RecentCommand) => {
      setRecent((previous) => {
        const withoutDuplicate = previous.filter((item) => item.id !== entry.id);
        return [entry, ...withoutDuplicate].slice(0, MAX_RECENT);
      });
    },
    [setRecent],
  );

  return { recent, addRecent };
}
