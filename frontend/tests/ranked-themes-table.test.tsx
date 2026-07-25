import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { RankedThemesTable } from "@/features/themes/RankedThemesTable";
import type { RankedTheme } from "@/features/themes/useThemesQuery";

const ROWS: RankedTheme[] = [
  {
    theme: "fraud_and_scams",
    signals: 120,
    volume: 150,
    severity_weighted: 20.5,
    corroborating_sources: 2,
    recent_volume: 80,
    previous_volume: 40,
  },
  {
    theme: "charges_and_fees",
    signals: 60,
    volume: 90,
    severity_weighted: 71.2,
    corroborating_sources: 1,
    recent_volume: 0,
    previous_volume: 30,
  },
];

function themeCells(): string[] {
  return screen.getAllByRole("row").slice(1).map((row) => row.children[1]?.textContent ?? "");
}

describe("RankedThemesTable", () => {
  it("ranks by volume and shows the half-year trend", () => {
    render(<RankedThemesTable rows={ROWS} weighting="volume" onSelect={vi.fn()} />);
    expect(themeCells()).toEqual(["Fraud and scams", "Charges and fees"]);
    expect(screen.getByText("+100%")).toBeInTheDocument();
    expect(screen.getByText("-100%")).toBeInTheDocument();
  });

  it("re-ranks when severity-weighted", () => {
    render(<RankedThemesTable rows={ROWS} weighting="severity" onSelect={vi.fn()} />);
    expect(themeCells()).toEqual(["Charges and fees", "Fraud and scams"]);
  });

  it("clicking a row drills into its theme", async () => {
    const onSelect = vi.fn();
    const user = userEvent.setup();
    render(<RankedThemesTable rows={ROWS} weighting="volume" onSelect={onSelect} />);
    await user.click(screen.getByText("Fraud and scams"));
    expect(onSelect).toHaveBeenCalledWith("fraud_and_scams");
  });

  it("explains an empty corpus", () => {
    render(<RankedThemesTable rows={[]} weighting="volume" onSelect={vi.fn()} />);
    expect(screen.getByText(/pf enrich run/)).toBeInTheDocument();
  });
});
