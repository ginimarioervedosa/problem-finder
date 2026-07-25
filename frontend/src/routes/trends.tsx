import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { FilterPanel } from "@/features/filters/FilterPanel";
import { useFilterStore } from "@/features/filters/filterStore";
import { TrendChart } from "@/features/trends/TrendChart";
import { useTrendQuery, type TrendDimension } from "@/features/trends/useTrendQuery";
import { useDebouncedValue } from "@/lib/useDebouncedValue";

const DIMENSIONS: { value: TrendDimension; label: string }[] = [
  { value: "category", label: "Category" },
  { value: "firm", label: "Firm" },
  { value: "source", label: "Source" },
];

export const Route = createFileRoute("/trends")({
  component: TrendsPage,
});

function TrendsPage() {
  const { search, firm, category, kind } = useFilterStore();
  const debouncedSearch = useDebouncedValue(search);
  const debouncedFirm = useDebouncedValue(firm);
  const [dimension, setDimension] = useState<TrendDimension>("category");

  const trend = useTrendQuery(dimension, {
    search: debouncedSearch || undefined,
    firm: debouncedFirm || undefined,
    category: category ?? undefined,
    kind: kind ?? undefined,
  });

  return (
    <div className="space-y-6">
      <FilterPanel categories={[]} />
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="text-base">Monthly volume by {dimension}</CardTitle>
          <div className="flex gap-2">
            {DIMENSIONS.map(({ value, label }) => (
              <Button
                key={value}
                size="sm"
                variant={value === dimension ? "default" : "outline"}
                onClick={() => {
                  setDimension(value);
                }}
              >
                {label}
              </Button>
            ))}
          </div>
        </CardHeader>
        <CardContent>
          <TrendChart points={trend.data} />
        </CardContent>
      </Card>
    </div>
  );
}
