import { keepPreviousData, useQuery } from "@tanstack/react-query";

import { api } from "@/api/client";
import type { operations } from "@/api/schema";

export type SignalsQuery = NonNullable<
  operations["list_signals_api_signals_get"]["parameters"]["query"]
>;

export function useSignalsQuery(query: SignalsQuery) {
  return useQuery({
    queryKey: ["signals", query],
    placeholderData: keepPreviousData,
    queryFn: async () => {
      const { data, error } = await api.GET("/api/signals", { params: { query } });
      if (error !== undefined) {
        throw new Error(`signals request failed: ${JSON.stringify(error)}`);
      }
      return data;
    },
  });
}
