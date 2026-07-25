import type { EChartsOption } from "echarts";
import { useMemo } from "react";

import { EChart } from "@/components/EChart";
import { Skeleton } from "@/components/ui/skeleton";
import { formatMonth } from "@/lib/format";

import { toTrendSeries } from "./trendSeries";
import type { TrendPoint } from "./useTrendQuery";

export function TrendChart({ points }: { points: TrendPoint[] | undefined }) {
  const option = useMemo<EChartsOption>(() => {
    const { months, lines } = toTrendSeries(points ?? []);
    return {
      grid: { left: 8, right: 24, top: 48, bottom: 8, containLabel: true },
      legend: { type: "scroll", top: 0 },
      xAxis: { type: "category", data: months.map(formatMonth) },
      yAxis: { type: "value", name: "volume" },
      tooltip: { trigger: "axis" },
      series: lines.map((line) => ({
        type: "line" as const,
        name: line.name,
        data: line.data,
        connectNulls: false,
        showSymbol: months.length < 30,
      })),
    };
  }, [points]);

  if (!points) {
    return <Skeleton className="h-96 w-full" />;
  }
  return <EChart option={option} height={384} />;
}
