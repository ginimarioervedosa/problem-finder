import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { RunsTable } from "@/features/runs/RunsTable";
import type { IngestionRun } from "@/features/runs/useRunsQuery";

function makeRun(overrides: Partial<IngestionRun> = {}): IngestionRun {
  return {
    id: "6c9a37a0-0000-4000-8000-000000000001",
    source_key: "fos_decisions",
    started_at: "2026-07-25T10:00:00Z",
    finished_at: "2026-07-25T10:02:30Z",
    fetched: 12,
    parsed: 12,
    stored_new: 10,
    deduplicated: 2,
    errors: [],
    ...overrides,
  };
}

describe("RunsTable", () => {
  it("shows counts, duration, and the source badge", () => {
    render(<RunsTable runs={[makeRun()]} />);
    expect(screen.getByText("fos_decisions")).toBeInTheDocument();
    expect(screen.getByText("2m 30s")).toBeInTheDocument();
    expect(screen.getByText("10")).toBeInTheDocument();
  });

  it("marks an unfinished run as running and surfaces error counts", () => {
    render(<RunsTable runs={[makeRun({ finished_at: null, errors: ["DRN-1: boom"] })]} />);
    expect(screen.getByText("running")).toBeInTheDocument();
    expect(screen.getByText("1")).toBeInTheDocument();
  });

  it("explains an empty ledger", () => {
    render(<RunsTable runs={[]} />);
    expect(screen.getByText(/No runs recorded yet/)).toBeInTheDocument();
  });
});
