import { createFileRoute } from "@tanstack/react-router";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { ThemeSuggestionsTable } from "@/features/suggestions/ThemeSuggestionsTable";
import { useThemeSuggestionsQuery } from "@/features/suggestions/useThemeSuggestionsQuery";

export const Route = createFileRoute("/suggestions")({
  component: SuggestionsPage,
});

function SuggestionsPage() {
  const suggestions = useThemeSuggestionsQuery();

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Suggested themes (ML clustering)</CardTitle>
      </CardHeader>
      <CardContent>
        {suggestions.data ? (
          <ThemeSuggestionsTable rows={suggestions.data} />
        ) : (
          <Skeleton className="h-96 w-full" />
        )}
      </CardContent>
    </Card>
  );
}
