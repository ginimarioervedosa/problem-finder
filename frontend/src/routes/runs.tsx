import { createFileRoute } from "@tanstack/react-router";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { RunsTable } from "@/features/runs/RunsTable";
import { useRunsQuery } from "@/features/runs/useRunsQuery";

export const Route = createFileRoute("/runs")({
  component: RunsPage,
});

function RunsPage() {
  const runs = useRunsQuery();

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Ingestion runs</CardTitle>
      </CardHeader>
      <CardContent>
        {runs.data ? <RunsTable runs={runs.data} /> : <Skeleton className="h-96 w-full" />}
      </CardContent>
    </Card>
  );
}
