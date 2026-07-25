import { keepPreviousData, useQuery } from "@tanstack/react-query";

import { api } from "@/api/client";
import type { components, operations } from "@/api/schema";

export type TrendPoint = components["schemas"]["TrendPoint"];
export type TrendDimension = components["schemas"]["SummaryDimension"];
export type TrendQuery = NonNullable<
  operations["trend_api_trends__dimension__get"]["parameters"]["query"]
>;

export function useTrendQuery(dimension: TrendDimension, query: TrendQuery) {
  return useQuery({
    queryKey: ["trends", dimension, query],
    placeholderData: keepPreviousData,
    queryFn: async () => {
      const { data, error } = await api.GET("/api/trends/{dimension}", {
        params: { path: { dimension }, query },
      });
      if (error !== undefined) {
        throw new Error(`trend request failed: ${JSON.stringify(error)}`);
      }
      return data;
    },
  });
}
