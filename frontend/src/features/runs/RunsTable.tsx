import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { formatCount, formatDateTime, formatDuration } from "@/lib/format";

import type { IngestionRun } from "./useRunsQuery";

const NUMERIC = "text-right tabular-nums";

export function RunsTable({ runs }: { runs: IngestionRun[] }) {
  return (
    <div className="rounded-md border bg-white">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Source</TableHead>
            <TableHead>Started</TableHead>
            <TableHead>Duration</TableHead>
            <TableHead className={NUMERIC}>Fetched</TableHead>
            <TableHead className={NUMERIC}>Parsed</TableHead>
            <TableHead className={NUMERIC}>Stored</TableHead>
            <TableHead className={NUMERIC}>Duplicates</TableHead>
            <TableHead className={NUMERIC}>Errors</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {runs.map((run) => (
            <TableRow key={run.id}>
              <TableCell>
                <Badge variant="secondary">{run.source_key}</Badge>
              </TableCell>
              <TableCell>{formatDateTime(run.started_at)}</TableCell>
              <TableCell>{formatDuration(run.started_at, run.finished_at)}</TableCell>
              <TableCell className={NUMERIC}>{formatCount(run.fetched)}</TableCell>
              <TableCell className={NUMERIC}>{formatCount(run.parsed)}</TableCell>
              <TableCell className={NUMERIC}>{formatCount(run.stored_new)}</TableCell>
              <TableCell className={NUMERIC}>{formatCount(run.deduplicated)}</TableCell>
              <TableCell className={NUMERIC} title={(run.errors ?? []).join("\n")}>
                {(run.errors ?? []).length > 0 ? (
                  <span className="font-medium text-red-700">{(run.errors ?? []).length}</span>
                ) : (
                  "0"
                )}
              </TableCell>
            </TableRow>
          ))}
          {runs.length === 0 && (
            <TableRow>
              <TableCell colSpan={8} className="text-center text-neutral-500">
                No runs recorded yet. Start one with `pf ingest run &lt;source&gt;`.
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
    </div>
  );
}
