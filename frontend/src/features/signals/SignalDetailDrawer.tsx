import { Badge } from "@/components/ui/badge";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { formatCount, formatDate, formatPeriod, formatShare } from "@/lib/format";

import { isAggregate, type Signal } from "./kinds";

interface SignalDetailDrawerProps {
  signal: Signal | null;
  onClose: () => void;
}

export function SignalDetailDrawer({ signal, onClose }: SignalDetailDrawerProps) {
  return (
    <Sheet
      open={signal !== null}
      onOpenChange={(open) => {
        if (!open) {
          onClose();
        }
      }}
    >
      <SheetContent className="w-[480px] overflow-y-auto sm:max-w-[480px]">
        {signal && <DrawerBody signal={signal} />}
      </SheetContent>
    </Sheet>
  );
}

function DrawerBody({ signal }: { signal: Signal }) {
  return (
    <>
      <SheetHeader>
        <div className="flex flex-wrap gap-2">
          <Badge variant="secondary">{signal.source_key}</Badge>
          <Badge variant="outline">{signal.kind}</Badge>
          {signal.category && <Badge variant="outline">{signal.category}</Badge>}
        </div>
        <SheetTitle>{signal.title ?? signal.firm_name ?? signal.external_id}</SheetTitle>
        <SheetDescription>{signal.body}</SheetDescription>
      </SheetHeader>
      <div className="space-y-6 px-4 pb-6">
        {isAggregate(signal) && (
          <dl className="grid grid-cols-3 gap-3 text-sm">
            <Metric label="Volume" value={formatCount(signal.volume)} />
            <Metric label="Upheld" value={formatShare(signal.upheld_share)} />
            <Metric label="Period" value={formatPeriod(signal.period_start, signal.period_end)} />
          </dl>
        )}
        <section className="space-y-1 text-sm">
          <h3 className="font-medium">Provenance</h3>
          <p className="text-muted-foreground">
            Retrieved {formatDate(signal.retrieved_at)} · adapter v
            {signal.provenance.adapter_version.toString()}
          </p>
          <p className="break-all font-mono text-xs text-muted-foreground">
            payload {signal.provenance.raw_payload_sha256.slice(0, 16)}… · run{" "}
            {signal.provenance.ingestion_run_id}
          </p>
          <a
            href={signal.url}
            target="_blank"
            rel="noreferrer"
            className="inline-block pt-1 font-medium text-neutral-900 underline underline-offset-4"
          >
            View the original source
          </a>
        </section>
      </div>
    </>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border bg-neutral-50 p-3">
      <dt className="text-xs text-muted-foreground">{label}</dt>
      <dd className="text-base font-semibold tabular-nums">{value}</dd>
    </div>
  );
}
