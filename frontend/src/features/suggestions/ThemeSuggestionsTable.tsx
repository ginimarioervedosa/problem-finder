import { Fragment, useState } from "react";

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

import type { ThemeSuggestion } from "./useThemeSuggestionsQuery";

const NUMERIC = "text-right tabular-nums";

const STATUS_VARIANT = {
  proposed: "secondary",
  accepted: "default",
  rejected: "outline",
} as const;

function mappingLabel(row: ThemeSuggestion): string {
  const theme = row.mapped_theme ?? row.suggested_theme;
  return theme === null ? "New territory" : formatThemeLabel(theme);
}

export function ThemeSuggestionsTable({ rows }: { rows: ThemeSuggestion[] }) {
  const [openId, setOpenId] = useState<string | null>(null);

  return (
    <div className="rounded-md border bg-white">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-16">Cluster</TableHead>
            <TableHead>Label</TableHead>
            <TableHead>Distinctive terms</TableHead>
            <TableHead>Maps onto</TableHead>
            <TableHead className={NUMERIC}>Signals</TableHead>
            <TableHead>Status</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {rows.map((row) => (
            <Fragment key={row.id}>
              <TableRow
                className="cursor-pointer"
                onClick={() => {
                  setOpenId(openId === row.id ? null : row.id);
                }}
              >
                <TableCell className="text-neutral-500">{row.cluster_key}</TableCell>
                <TableCell className="font-medium">{formatThemeLabel(row.label)}</TableCell>
                <TableCell className="text-neutral-600">
                  {row.top_terms.slice(0, 5).join(", ")}
                </TableCell>
                <TableCell>{mappingLabel(row)}</TableCell>
                <TableCell className={NUMERIC}>{formatCount(row.size)}</TableCell>
                <TableCell>
                  <Badge variant={STATUS_VARIANT[row.status]}>{row.status}</Badge>
                </TableCell>
              </TableRow>
              {openId === row.id && (
                <TableRow>
                  <TableCell colSpan={6} className="bg-neutral-50">
                    <div className="space-y-2 py-1">
                      {row.representatives.map((representative) => (
                        <p key={representative.id} className="text-sm text-neutral-600">
                          <span className="font-medium text-neutral-800">
                            {representative.title ?? "Untitled"}:{" "}
                          </span>
                          {representative.snippet}…
                        </p>
                      ))}
                      {row.status === "proposed" && (
                        <p className="text-xs text-neutral-500">
                          Review from the CLI: `pf ml accept {row.cluster_key}` or `pf ml reject{" "}
                          {row.cluster_key}`.
                        </p>
                      )}
                    </div>
                  </TableCell>
                </TableRow>
              )}
            </Fragment>
          ))}
          {rows.length === 0 && (
            <TableRow>
              <TableCell colSpan={6} className="text-center text-neutral-500">
                No suggestions yet. Propose them with `pf ml cluster` (needs the ml extras).
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
    </div>
  );
}
