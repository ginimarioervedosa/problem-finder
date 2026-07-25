import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useFilterStore } from "@/features/filters/filterStore";
import { RankedThemesTable, type Weighting } from "@/features/themes/RankedThemesTable";
import { useThemesQuery } from "@/features/themes/useThemesQuery";

export const Route = createFileRoute("/themes")({
  component: ThemesPage,
});

const WEIGHTINGS: { value: Weighting; label: string }[] = [
  { value: "volume", label: "Volume-weighted" },
  { value: "severity", label: "Severity-weighted" },
];

function ThemesPage() {
  const themes = useThemesQuery();
  const [weighting, setWeighting] = useState<Weighting>("volume");
  const setTheme = useFilterStore((state) => state.setTheme);
  const navigate = useNavigate();

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between">
        <CardTitle className="text-base">Ranked problem themes</CardTitle>
        <div className="flex gap-1">
          {WEIGHTINGS.map((option) => (
            <Button
              key={option.value}
              size="sm"
              variant={weighting === option.value ? "default" : "outline"}
              onClick={() => {
                setWeighting(option.value);
              }}
            >
              {option.label}
            </Button>
          ))}
        </div>
      </CardHeader>
      <CardContent>
        {themes.data ? (
          <RankedThemesTable
            rows={themes.data}
            weighting={weighting}
            onSelect={(theme) => {
              setTheme(theme); // drill: the signals view opens on this theme's verbatims
              void navigate({ to: "/signals" });
            }}
          />
        ) : (
          <Skeleton className="h-96 w-full" />
        )}
      </CardContent>
    </Card>
  );
}
