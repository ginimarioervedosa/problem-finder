// Date and number formatting lives here and only here.

const numberFormat = new Intl.NumberFormat("en-GB");
const dateFormat = new Intl.DateTimeFormat("en-GB", { dateStyle: "medium" });
const dateTimeFormat = new Intl.DateTimeFormat("en-GB", {
  dateStyle: "medium",
  timeStyle: "short",
});
const monthFormat = new Intl.DateTimeFormat("en-GB", { month: "short", year: "numeric" });

export function formatCount(value: number | null | undefined): string {
  return value == null ? "—" : numberFormat.format(value);
}

export function formatShare(value: number | null | undefined): string {
  return value == null ? "—" : `${Math.round(value * 100).toString()}%`;
}

export function formatDate(value: string | null | undefined): string {
  return value ? dateFormat.format(new Date(value)) : "—";
}

export function formatDateTime(value: string | null | undefined): string {
  return value ? dateTimeFormat.format(new Date(value)) : "—";
}

export function formatMonth(value: string): string {
  return monthFormat.format(new Date(value));
}

export function formatDuration(start: string, end: string | null | undefined): string {
  if (!end) {
    return "running";
  }
  const seconds = (new Date(end).getTime() - new Date(start).getTime()) / 1000;
  if (seconds < 60) {
    return `${seconds.toFixed(seconds < 10 ? 1 : 0)}s`;
  }
  return `${Math.floor(seconds / 60).toString()}m ${Math.round(seconds % 60).toString()}s`;
}

export function formatPeriod(start: string | null | undefined, end: string | null | undefined): string {
  if (!start || !end) {
    return "—";
  }
  const half = new Date(start).getMonth() < 6 ? "H1" : "H2";
  return `${half} ${new Date(end).getFullYear().toString()}`;
}
