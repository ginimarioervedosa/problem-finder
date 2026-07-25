import {
  createColumnHelper,
  flexRender,
  getCoreRowModel,
  useReactTable,
} from "@tanstack/react-table";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { formatCount, formatDate, formatPeriod, formatShare } from "@/lib/format";

import { isAggregate, type Signal } from "./kinds";

const columnHelper = createColumnHelper<Signal>();

const columns = [
  columnHelper.accessor((signal) => signal.firm_name ?? signal.title ?? "—", {
    id: "subject",
    header: "Firm / subject",
    cell: (cell) => <span className="font-medium">{cell.getValue()}</span>,
  }),
  columnHelper.accessor((signal) => signal.category ?? "—", { id: "category", header: "Category" }),
  columnHelper.accessor(
    (signal) =>
      isAggregate(signal)
        ? formatPeriod(signal.period_start, signal.period_end)
        : formatDate(signal.published_at),
    { id: "period", header: "Period" },
  ),
  columnHelper.accessor((signal) => (isAggregate(signal) ? signal.volume : null), {
    id: "volume",
    header: () => <span className="block text-right">Volume</span>,
    cell: (cell) => <span className="block text-right tabular-nums">{formatCount(cell.getValue())}</span>,
  }),
  columnHelper.accessor((signal) => (isAggregate(signal) ? signal.upheld_share : null), {
    id: "upheld",
    header: () => <span className="block text-right">Upheld</span>,
    cell: (cell) => <span className="block text-right tabular-nums">{formatShare(cell.getValue())}</span>,
  }),
  columnHelper.accessor("source_key", {
    id: "source",
    header: "Source",
    cell: (cell) => <Badge variant="secondary">{cell.getValue()}</Badge>,
  }),
];

interface SignalsTableProps {
  signals: Signal[];
  total: number;
  pageIndex: number;
  pageSize: number;
  onPageChange: (pageIndex: number) => void;
  onSelect: (signal: Signal) => void;
}

export function SignalsTable(props: SignalsTableProps) {
  const { signals, total, pageIndex, pageSize, onPageChange, onSelect } = props;
  const table = useReactTable({ data: signals, columns, getCoreRowModel: getCoreRowModel() });
  const pageCount = Math.max(1, Math.ceil(total / pageSize));

  return (
    <div className="space-y-3">
      <div className="rounded-md border bg-white">
        <Table>
          <TableHeader>
            {table.getHeaderGroups().map((headerGroup) => (
              <TableRow key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <TableHead key={header.id}>
                    {flexRender(header.column.columnDef.header, header.getContext())}
                  </TableHead>
                ))}
              </TableRow>
            ))}
          </TableHeader>
          <TableBody>
            {table.getRowModel().rows.map((row) => (
              <TableRow
                key={row.id}
                className="cursor-pointer"
                onClick={() => {
                  onSelect(row.original);
                }}
              >
                {row.getVisibleCells().map((cell) => (
                  <TableCell key={cell.id}>
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </TableCell>
                ))}
              </TableRow>
            ))}
            {signals.length === 0 && (
              <TableRow>
                <TableCell colSpan={columns.length} className="py-10 text-center text-muted-foreground">
                  No signals match the current filters.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
      <div className="flex items-center justify-between text-sm text-muted-foreground">
        <span>
          {formatCount(total)} signals · page {pageIndex + 1} of {pageCount}
        </span>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            disabled={pageIndex === 0}
            onClick={() => {
              onPageChange(pageIndex - 1);
            }}
          >
            Previous
          </Button>
          <Button
            variant="outline"
            size="sm"
            disabled={pageIndex + 1 >= pageCount}
            onClick={() => {
              onPageChange(pageIndex + 1);
            }}
          >
            Next
          </Button>
        </div>
      </div>
    </div>
  );
}
