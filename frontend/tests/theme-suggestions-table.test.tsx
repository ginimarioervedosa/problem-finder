import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { ThemeSuggestionsTable } from "@/features/suggestions/ThemeSuggestionsTable";
import type { ThemeSuggestion } from "@/features/suggestions/useThemeSuggestionsQuery";

const ROWS: ThemeSuggestion[] = [
  {
    id: "11111111-1111-4111-8111-111111111111",
    cluster_key: 0,
    label: "transfer_delay_pension",
    method: "hdbscan:v1",
    size: 42,
    top_terms: ["transfer", "delay", "pension", "sipp", "provider", "extra"],
    suggested_theme: "delays_and_service_failures",
    status: "proposed",
    mapped_theme: null,
    created_at: "2026-07-25T12:00:00Z",
    decided_at: null,
    representatives: [
      {
        id: "22222222-2222-4222-8222-222222222222",
        title: "DRN-0000001",
        snippet: "The SIPP transfer took eleven months",
      },
    ],
  },
  {
    id: "33333333-3333-4333-8333-333333333333",
    cluster_key: 1,
    label: "crypto_wallet_loss",
    method: "hdbscan:v1",
    size: 17,
    top_terms: ["crypto", "wallet", "exchange"],
    suggested_theme: null,
    status: "accepted",
    mapped_theme: "crypto_wallet_loss",
    created_at: "2026-07-25T12:00:00Z",
    decided_at: "2026-07-25T13:00:00Z",
    representatives: [],
  },
];

describe("ThemeSuggestionsTable", () => {
  it("shows label, terms, size and mapping per cluster", () => {
    render(<ThemeSuggestionsTable rows={ROWS} />);
    expect(screen.getByText("Transfer delay pension")).toBeInTheDocument();
    expect(screen.getByText("transfer, delay, pension, sipp, provider")).toBeInTheDocument();
    expect(screen.getByText("Delays and service failures")).toBeInTheDocument();
    expect(screen.getByText("42")).toBeInTheDocument();
  });

  it("badges the review status and shows the accepted mapping", () => {
    render(<ThemeSuggestionsTable rows={ROWS} />);
    expect(screen.getByText("proposed")).toBeInTheDocument();
    expect(screen.getByText("accepted")).toBeInTheDocument();
    // Label and accepted mapping are the same name here: once per column.
    expect(screen.getAllByText("Crypto wallet loss")).toHaveLength(2);
  });

  it("expands a row into its representative verbatims and review hint", async () => {
    const user = userEvent.setup();
    render(<ThemeSuggestionsTable rows={ROWS} />);
    await user.click(screen.getByText("Transfer delay pension"));
    expect(screen.getByText(/The SIPP transfer took eleven months/)).toBeInTheDocument();
    expect(screen.getByText(/pf ml accept 0/)).toBeInTheDocument();
  });

  it("explains an empty list", () => {
    render(<ThemeSuggestionsTable rows={[]} />);
    expect(screen.getByText(/pf ml cluster/)).toBeInTheDocument();
  });
});
