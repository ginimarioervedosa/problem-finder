// Pivot the API's flat (bucket, key, volume) points into chart series:
// one x-axis of months, one line per key, null where a key has no bucket.
import type { TrendPoint } from "./useTrendQuery";

export interface TrendSeries {
  months: string[];
  lines: { name: string; data: (number | null)[] }[];
}

export function toTrendSeries(points: TrendPoint[]): TrendSeries {
  const months = [...new Set(points.map((point) => point.bucket))].sort();
  const keys = [...new Set(points.map((point) => point.key))];
  const volumes = new Map(points.map((point) => [`${point.bucket}|${point.key}`, point.volume]));
  return {
    months,
    lines: keys.map((key) => ({
      name: key,
      data: months.map((month) => volumes.get(`${month}|${key}`) ?? null),
    })),
  };
}
