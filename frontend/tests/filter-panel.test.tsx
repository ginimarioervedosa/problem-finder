import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it } from "vitest";

import { FilterPanel } from "@/features/filters/FilterPanel";
import { useFilterStore } from "@/features/filters/filterStore";

describe("FilterPanel", () => {
  beforeEach(() => {
    useFilterStore.getState().reset();
  });

  it("wires the search box into the filter store", async () => {
    const user = userEvent.setup();
    render(<FilterPanel categories={["Banking and Payments"]} />);
    await user.type(screen.getByLabelText("Search signal text"), "scam refund");
    expect(useFilterStore.getState().search).toBe("scam refund");
  });

  it("reset clears the search alongside the other filters", async () => {
    const user = userEvent.setup();
    render(<FilterPanel categories={[]} />);
    await user.type(screen.getByLabelText("Search signal text"), "sipp");
    await user.type(screen.getByLabelText("Filter by firm"), "Alpha");
    await user.click(screen.getByRole("button", { name: "Reset" }));
    expect(useFilterStore.getState().search).toBe("");
    expect(useFilterStore.getState().firm).toBe("");
  });
});
