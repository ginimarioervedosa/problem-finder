// Client state only: what the user has dialled in. Server data never lives here.
import { create } from "zustand";

import type { components } from "@/api/schema";

type SignalKind = components["schemas"]["SignalKind"];

interface FilterState {
  search: string;
  firm: string;
  category: string | null;
  kind: SignalKind | null;
  theme: string | null;
  setSearch: (search: string) => void;
  setFirm: (firm: string) => void;
  setCategory: (category: string | null) => void;
  setKind: (kind: SignalKind | null) => void;
  setTheme: (theme: string | null) => void;
  reset: () => void;
}

export const useFilterStore = create<FilterState>()((set) => ({
  search: "",
  firm: "",
  category: null,
  kind: null,
  theme: null,
  setSearch: (search) => {
    set({ search });
  },
  setFirm: (firm) => {
    set({ firm });
  },
  setCategory: (category) => {
    set({ category });
  },
  setKind: (kind) => {
    set({ kind });
  },
  setTheme: (theme) => {
    set({ theme });
  },
  reset: () => {
    set({ search: "", firm: "", category: null, kind: null, theme: null });
  },
}));
