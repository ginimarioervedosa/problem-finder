import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { formatCount, formatThemeLabel } from "@/lib/format";

import type { RankedTheme } from "./useThemesQuery";

export type Weighting = "volume" | "severity";

const NUMERIC = "text-right tabular-nums";

// Recent half-year against the one before; "new" when the theme had no history.
function trendLabel(recent: number, previous: number): string {
  if (previous === 0) {
    return recent > 0 ? "new" : "—";
  }
  const pct = Math.round(((recent - previous) / previous) * 100);
  return `${pct > 0 ? "+" : ""}${pct.toString()}%`;
}

function ranked(rows: RankedTheme[], weighting: Weighting): RankedTheme[] {
  return [...rows].sort((a, b) =>
    weighting === "volume" ? b.volume - a.volume : b.severity_weighted - a.severity_weighted,
  );
}

export function RankedThemesTable({
  rows,
  weighting,
  onSelect,
}: {
  rows: RankedTheme[];
  weighting: Weighting;
  onSelect: (theme: string) => void;
}) {
  return (
    <div className="rounded-md border bg-white">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-10">#</TableHead>
            <TableHead>Theme</TableHead>
            <TableHead className={NUMERIC}>Signals</TableHead>
            <TableHead className={NUMERIC}>Volume</TableHead>
            <TableHead className={NUMERIC}>Severity-weighted</TableHead>
            <TableHead className={NUMERIC}>Sources</TableHead>
            <TableHead className={NUMERIC}>Trend</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {ranked(rows, weighting).map((row, index) => (
            <TableRow
              key={row.theme}
              className="cursor-pointer"
              onClick={() => {
                onSelect(row.theme);
              }}
            >
              <TableCell className="text-neutral-500">{index + 1}</TableCell>
              <TableCell className="font-medium">{formatThemeLabel(row.theme)}</TableCell>
              <TableCell className={NUMERIC}>{formatCount(row.signals)}</TableCell>
              <TableCell className={NUMERIC}>{formatCount(row.volume)}</TableCell>
              <TableCell className={NUMERIC}>{row.severity_weighted.toFixed(1)}</TableCell>
              <TableCell className={NUMERIC}>
                <Badge variant="secondary">{row.corroborating_sources}</Badge>
              </TableCell>
              <TableCell className={NUMERIC}>
                {trendLabel(row.recent_volume, row.previous_volume)}
              </TableCell>
            </TableRow>
          ))}
          {rows.length === 0 && (
            <TableRow>
              <TableCell colSpan={7} className="text-center text-neutral-500">
                No themes yet. Compute them with `pf enrich run`.
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
    </div>
  );
}
