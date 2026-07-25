// The signal union as the frontend sees it, plus the discriminator guard.
import type { components } from "@/api/schema";

export type VerbatimSignal = components["schemas"]["VerbatimSignal"];
export type AggregateSignal = components["schemas"]["AggregateSignal"];
export type Signal = VerbatimSignal | AggregateSignal;

export function isAggregate(signal: Signal): signal is AggregateSignal {
  return signal.kind === "aggregate";
}
