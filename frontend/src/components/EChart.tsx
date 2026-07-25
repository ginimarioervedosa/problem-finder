// Minimal ECharts wrapper: init once, setOption on change, dispose on unmount.
import * as echarts from "echarts";
import { useEffect, useRef } from "react";

interface EChartProps {
  option: echarts.EChartsOption;
  onBarClick?: (name: string) => void;
  height?: number;
}

export function EChart({ option, onBarClick, height = 320 }: EChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<echarts.ECharts | null>(null);
  const clickRef = useRef(onBarClick);
  clickRef.current = onBarClick;

  useEffect(() => {
    if (!containerRef.current) {
      return;
    }
    const chart = echarts.init(containerRef.current);
    chartRef.current = chart;
    chart.on("click", (params) => {
      if (typeof params.name === "string" && clickRef.current) {
        clickRef.current(params.name);
      }
    });
    const observer = new ResizeObserver(() => {
      chart.resize();
    });
    observer.observe(containerRef.current);
    return () => {
      observer.disconnect();
      chart.dispose();
      chartRef.current = null;
    };
  }, []);

  useEffect(() => {
    chartRef.current?.setOption(option, { notMerge: true });
  }, [option]);

  return <div ref={containerRef} style={{ height }} />;
}
