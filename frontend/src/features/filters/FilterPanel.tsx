import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { formatThemeLabel } from "@/lib/format";

import { useFilterStore } from "./filterStore";

const KINDS = [
  { value: "", label: "All kinds" },
  { value: "aggregate", label: "Aggregate" },
  { value: "verbatim", label: "Verbatim" },
] as const;

const selectClass =
  "h-9 rounded-md border border-input bg-transparent px-3 text-sm shadow-xs outline-none focus-visible:ring-[3px] focus-visible:ring-ring/50";

export function FilterPanel({ categories }: { categories: string[] }) {
  const { search, firm, category, kind, theme, ...actions } = useFilterStore();
  const { setSearch, setFirm, setCategory, setKind, setTheme, reset } = actions;
  return (
    <div className="flex flex-wrap items-center gap-3">
      <Input
        type="search"
        value={search}
        onChange={(event) => {
          setSearch(event.target.value);
        }}
        placeholder="Search signal text…"
        className="w-72"
        aria-label="Search signal text"
      />
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
      {theme !== null && (
        <Badge variant="secondary" className="gap-1">
          Theme: {formatThemeLabel(theme)}
          <button
            type="button"
            aria-label="Clear theme filter"
            className="cursor-pointer font-semibold"
            onClick={() => {
              setTheme(null);
            }}
          >
            ×
          </button>
        </Badge>
      )}
      <Button variant="ghost" size="sm" onClick={reset}>
        Reset
      </Button>
    </div>
  );
}
