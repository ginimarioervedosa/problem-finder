import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { SignalsTable } from "@/features/signals/SignalsTable";
import type { AggregateSignal, VerbatimSignal } from "@/features/signals/kinds";

const provenance = {
  raw_payload_sha256: "a".repeat(64),
  adapter_version: 1,
  ingestion_run_id: "3f0e6f60-2f2a-4640-a840-90ad3f5b4e2e",
  fetched_at: "2026-07-25T09:00:00Z",
};

const aggregate: AggregateSignal = {
  kind: "aggregate",
  id: "e7cd2e08-96a2-5d18-a9a1-1e6b3cb1a5b4",
  source_key: "fos_complaints",
  external_id: "h1-2025:alpha-bank:banking",
  url: "https://example.org/release",
  published_at: null,
  retrieved_at: "2026-07-25T09:00:00Z",
  title: "Alpha Bank: Banking & Credit complaints, H1 2025",
  body: "Alpha Bank received 140 new Banking & Credit complaints.",
  language: "en",
  firm_name: "Alpha Bank",
  category: "Banking & Credit",
  extras: {},
  provenance,
  period_start: "2025-01-01",
  period_end: "2025-06-30",
  volume: 140,
  upheld_share: 0.45,
  denominator: null,
};

const verbatim: VerbatimSignal = {
  kind: "verbatim",
  id: "1c1e9ae4-51a5-5cd2-a2eb-5d4093a7d0a8",
  source_key: "reddit",
  external_id: "t3_abc",
  url: "https://example.org/post",
  published_at: "2026-06-01T12:00:00Z",
  retrieved_at: "2026-07-25T09:00:00Z",
  title: "SIPP transfer stuck",
  body: "My SIPP transfer has been stuck for months.",
  language: "en",
  firm_name: null,
  category: "Investments",
  extras: {},
  provenance,
  author_handle: "some_user",
};

describe("SignalsTable", () => {
  it("renders both signal kinds with their metrics", () => {
    render(
      <SignalsTable
        signals={[aggregate, verbatim]}
        total={2}
        pageIndex={0}
        pageSize={25}
        onPageChange={vi.fn()}
        onSelect={vi.fn()}
      />,
    );
    expect(screen.getByText("Alpha Bank")).toBeInTheDocument();
    expect(screen.getByText("140")).toBeInTheDocument();
    expect(screen.getByText("45%")).toBeInTheDocument();
    expect(screen.getByText("SIPP transfer stuck")).toBeInTheDocument();
    expect(screen.getByText("H1 2025")).toBeInTheDocument();
  });

  it("drills into a row via onSelect", async () => {
    const onSelect = vi.fn();
    const user = userEvent.setup();
    render(
      <SignalsTable
        signals={[aggregate]}
        total={1}
        pageIndex={0}
        pageSize={25}
        onPageChange={vi.fn()}
        onSelect={onSelect}
      />,
    );
    await user.click(screen.getByText("Alpha Bank"));
    expect(onSelect).toHaveBeenCalledWith(aggregate);
  });

  it("disables pagination at the bounds", () => {
    render(
      <SignalsTable
        signals={[aggregate]}
        total={1}
        pageIndex={0}
        pageSize={25}
        onPageChange={vi.fn()}
        onSelect={vi.fn()}
      />,
    );
    expect(screen.getByRole("button", { name: "Previous" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Next" })).toBeDisabled();
  });
});
