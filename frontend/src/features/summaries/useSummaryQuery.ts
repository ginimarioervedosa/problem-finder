import { keepPreviousData, useQuery } from "@tanstack/react-query";

import { api } from "@/api/client";
import type { components, operations } from "@/api/schema";

export type SummaryRow = components["schemas"]["SummaryRow"];
export type SummaryDimension = components["schemas"]["SummaryDimension"];
export type SummaryQuery = NonNullable<
  operations["summarise_api_summaries__dimension__get"]["parameters"]["query"]
>;

export function useSummaryQuery(dimension: SummaryDimension, query: SummaryQuery) {
  return useQuery({
    queryKey: ["summaries", dimension, query],
    placeholderData: keepPreviousData,
    queryFn: async () => {
      const { data, error } = await api.GET("/api/summaries/{dimension}", {
        params: { path: { dimension }, query },
      });
      if (error !== undefined) {
        throw new Error(`summary request failed: ${JSON.stringify(error)}`);
      }
      return data;
    },
  });
}
