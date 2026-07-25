import { keepPreviousData, useQuery } from "@tanstack/react-query";

import { api } from "@/api/client";
import type { components } from "@/api/schema";

export type RankedTheme = components["schemas"]["RankedTheme"];

export function useThemesQuery() {
  return useQuery({
    queryKey: ["themes"],
    placeholderData: keepPreviousData,
    queryFn: async () => {
      const { data, error } = await api.GET("/api/themes", {});
      if (error !== undefined) {
        throw new Error(`themes request failed: ${JSON.stringify(error)}`);
      }
      return data;
    },
  });
}
