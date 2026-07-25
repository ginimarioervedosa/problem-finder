// Client state only: what the user has dialled in. Server data never lives here.
import { create } from "zustand";

import type { components } from "@/api/schema";

type SignalKind = components["schemas"]["SignalKind"];

interface FilterState {
  firm: string;
  category: string | null;
  kind: SignalKind | null;
  setFirm: (firm: string) => void;
  setCategory: (category: string | null) => void;
  setKind: (kind: SignalKind | null) => void;
  reset: () => void;
}

export const useFilterStore = create<FilterState>()((set) => ({
  firm: "",
  category: null,
  kind: null,
  setFirm: (firm) => {
    set({ firm });
  },
  setCategory: (category) => {
    set({ category });
  },
  setKind: (kind) => {
    set({ kind });
  },
  reset: () => {
    set({ firm: "", category: null, kind: null });
  },
}));
