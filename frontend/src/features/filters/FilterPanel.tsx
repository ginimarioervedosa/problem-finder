import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

import { useFilterStore } from "./filterStore";

const KINDS = [
  { value: "", label: "All kinds" },
  { value: "aggregate", label: "Aggregate" },
  { value: "verbatim", label: "Verbatim" },
] as const;

const selectClass =
  "h-9 rounded-md border border-input bg-transparent px-3 text-sm shadow-xs outline-none focus-visible:ring-[3px] focus-visible:ring-ring/50";

export function FilterPanel({ categories }: { categories: string[] }) {
  const { firm, category, kind, setFirm, setCategory, setKind, reset } = useFilterStore();
  return (
    <div className="flex flex-wrap items-center gap-3">
      <Input
        value={firm}
        onChange={(event) => {
          setFirm(event.target.value);
        }}
        placeholder="Filter by firm…"
        className="w-64"
        aria-label="Filter by firm"
      />
      <select
        value={category ?? ""}
        onChange={(event) => {
          setCategory(event.target.value || null);
        }}
        className={selectClass}
        aria-label="Filter by category"
      >
        <option value="">All categories</option>
        {categories.map((name) => (
          <option key={name} value={name}>
            {name}
          </option>
        ))}
      </select>
      <select
        value={kind ?? ""}
        onChange={(event) => {
          setKind(event.target.value === "" ? null : (event.target.value as "aggregate" | "verbatim"));
        }}
        className={selectClass}
        aria-label="Filter by kind"
      >
        {KINDS.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
      <Button variant="ghost" size="sm" onClick={reset}>
        Reset
      </Button>
    </div>
  );
}
