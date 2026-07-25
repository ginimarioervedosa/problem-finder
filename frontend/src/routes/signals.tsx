import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { FilterPanel } from "@/features/filters/FilterPanel";
import { useFilterStore } from "@/features/filters/filterStore";
import { SignalDetailDrawer } from "@/features/signals/SignalDetailDrawer";
import { SignalsTable } from "@/features/signals/SignalsTable";
import type { Signal } from "@/features/signals/kinds";
import { useSignalsQuery } from "@/features/signals/useSignalsQuery";
import { VolumeByDimensionChart } from "@/features/summaries/VolumeByDimensionChart";
import { useSummaryQuery } from "@/features/summaries/useSummaryQuery";
import { useDebouncedValue } from "@/lib/useDebouncedValue";

const PAGE_SIZE = 25;

export const Route = createFileRoute("/signals")({
  component: SignalsPage,
});

function SignalsPage() {
  const { search, firm, category, kind, setCategory } = useFilterStore();
  const debouncedSearch = useDebouncedValue(search);
  const debouncedFirm = useDebouncedValue(firm);
  const filterQuery = {
    search: debouncedSearch || undefined,
    firm: debouncedFirm || undefined,
    category: category ?? undefined,
    kind: kind ?? undefined,
  };

  const [pageIndex, setPageIndex] = useState(0);
  useEffect(() => {
    setPageIndex(0);
  }, [debouncedSearch, debouncedFirm, category, kind]);

  const signals = useSignalsQuery({
    ...filterQuery,
    limit: PAGE_SIZE,
    offset: pageIndex * PAGE_SIZE,
  });
  const categorySummary = useSummaryQuery("category", {
    search: filterQuery.search,
    firm: filterQuery.firm,
    kind: filterQuery.kind,
  });
  const [selected, setSelected] = useState<Signal | null>(null);

  const categories = (categorySummary.data ?? []).map((row) => row.key);

  return (
    <div className="space-y-6">
      <FilterPanel categories={categories} />
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Complaint volume by category</CardTitle>
        </CardHeader>
        <CardContent>
          <VolumeByDimensionChart
            rows={categorySummary.data}
            onBarClick={(key) => {
              setCategory(key === category ? null : key);
            }}
          />
        </CardContent>
      </Card>
      {signals.data ? (
        <SignalsTable
          signals={signals.data.items}
          total={signals.data.total}
          pageIndex={pageIndex}
          pageSize={PAGE_SIZE}
          onPageChange={setPageIndex}
          onSelect={setSelected}
        />
      ) : (
        <Skeleton className="h-96 w-full" />
      )}
      <SignalDetailDrawer
        signal={selected}
        onClose={() => {
          setSelected(null);
        }}
      />
    </div>
  );
}
