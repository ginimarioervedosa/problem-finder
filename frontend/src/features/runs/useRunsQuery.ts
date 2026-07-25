import { keepPreviousData, useQuery } from "@tanstack/react-query";

import { api } from "@/api/client";
import type { components } from "@/api/schema";

export type IngestionRun = components["schemas"]["IngestionRun"];

export function useRunsQuery() {
  return useQuery({
    queryKey: ["runs"],
    placeholderData: keepPreviousData,
    refetchInterval: 30_000, // a worker may be ingesting in the background
    queryFn: async () => {
      const { data, error } = await api.GET("/api/runs", {});
      if (error !== undefined) {
        throw new Error(`runs request failed: ${JSON.stringify(error)}`);
      }
      return data;
    },
  });
}
