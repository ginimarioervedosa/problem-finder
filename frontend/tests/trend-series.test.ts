import { describe, expect, it } from "vitest";

import { toTrendSeries } from "@/features/trends/trendSeries";

const POINTS = [
  { bucket: "2025-06-01", key: "Banking & Credit", volume: 61, signals: 2 },
  { bucket: "2025-12-01", key: "Banking & Credit", volume: 40, signals: 1 },
  { bucket: "2025-06-01", key: "Investments", volume: 10, signals: 1 },
];

describe("toTrendSeries", () => {
  it("pivots points into one line per key over a shared month axis", () => {
    const { months, lines } = toTrendSeries(POINTS);
    expect(months).toEqual(["2025-06-01", "2025-12-01"]);
    expect(lines).toEqual([
      { name: "Banking & Credit", data: [61, 40] },
      { name: "Investments", data: [10, null] },
    ]);
  });

  it("handles an empty result", () => {
    expect(toTrendSeries([])).toEqual({ months: [], lines: [] });
  });
});
