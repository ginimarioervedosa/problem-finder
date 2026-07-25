// Date and number formatting lives here and only here.

const numberFormat = new Intl.NumberFormat("en-GB");
const dateFormat = new Intl.DateTimeFormat("en-GB", { dateStyle: "medium" });

export function formatCount(value: number | null | undefined): string {
  return value == null ? "—" : numberFormat.format(value);
}

export function formatShare(value: number | null | undefined): string {
  return value == null ? "—" : `${Math.round(value * 100).toString()}%`;
}

export function formatDate(value: string | null | undefined): string {
  return value ? dateFormat.format(new Date(value)) : "—";
}

export function formatPeriod(start: string | null | undefined, end: string | null | undefined): string {
  if (!start || !end) {
    return "—";
  }
  const half = new Date(start).getMonth() < 6 ? "H1" : "H2";
  return `${half} ${new Date(end).getFullYear().toString()}`;
}
