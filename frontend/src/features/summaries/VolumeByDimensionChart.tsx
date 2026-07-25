import type { EChartsOption } from "echarts";
import { useMemo } from "react";

import { EChart } from "@/components/EChart";
import { Skeleton } from "@/components/ui/skeleton";

import type { SummaryRow } from "./useSummaryQuery";

interface VolumeByDimensionChartProps {
  rows: SummaryRow[] | undefined;
  onBarClick?: (key: string) => void;
}

export function VolumeByDimensionChart({ rows, onBarClick }: VolumeByDimensionChartProps) {
  const option = useMemo<EChartsOption>(() => {
    const ordered = [...(rows ?? [])].reverse();
    return {
      grid: { left: 8, right: 48, top: 8, bottom: 8, containLabel: true },
      xAxis: { type: "value", name: "complaints", nameLocation: "end" },
      yAxis: {
        type: "category",
        data: ordered.map((row) => row.key),
        axisLabel: { width: 220, overflow: "truncate" },
      },
      tooltip: { trigger: "axis", axisPointer: { type: "shadow" } },
      series: [
        {
          type: "bar",
          data: ordered.map((row) => row.volume),
          itemStyle: { color: "#404040" },
          label: { show: true, position: "right", formatter: "{c}" },
        },
      ],
    };
  }, [rows]);

  if (!rows) {
    return <Skeleton className="h-80 w-full" />;
  }
  return <EChart option={option} onBarClick={onBarClick} height={320} />;
}
