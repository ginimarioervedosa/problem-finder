import { keepPreviousData, useQuery } from "@tanstack/react-query";

import { api } from "@/api/client";
import type { components } from "@/api/schema";

export type ThemeSuggestion = components["schemas"]["ThemeSuggestionView"];

export function useThemeSuggestionsQuery() {
  return useQuery({
    queryKey: ["theme-suggestions"],
    placeholderData: keepPreviousData,
    queryFn: async () => {
      const { data, error } = await api.GET("/api/theme-suggestions", {});
      if (error !== undefined) {
        throw new Error(`theme suggestions request failed: ${JSON.stringify(error)}`);
      }
      return data;
    },
  });
}
