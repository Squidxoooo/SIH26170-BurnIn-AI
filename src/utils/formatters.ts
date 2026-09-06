import type { Status } from "@/types";

export const PARAMETER_UNITS: Record<string, string> = {
  Iddq: "µA",
  LeakageCurrent: "µA",
  PropDelay: "ns",
  VthDrift: "mV",
};

export const PARAMETER_LABELS: Record<string, string> = {
  Iddq: "Quiescent Current",
  LeakageCurrent: "Leakage Current",
  PropDelay: "Propagation Delay",
  VthDrift: "Threshold Voltage Drift",
};

export const unitFor = (parameter: string) => PARAMETER_UNITS[parameter] ?? "";

export const num = (v: number | null | undefined, digits = 2) =>
  v === null || v === undefined || Number.isNaN(v) ? "—" : v.toFixed(digits);

export const withUnit = (v: number | null | undefined, unit: string, digits = 2) =>
  v === null || v === undefined || Number.isNaN(v) ? "—" : `${v.toFixed(digits)} ${unit}`;

export const STATUS_LABEL: Record<Status, string> = {
  SAFE: "SAFE",
  MONITOR: "MONITOR",
  FURTHER_TESTING: "FURTHER TESTING",
  CRITICAL: "CRITICAL",
};

export const STATUS_COLOR: Record<Status, string> = {
  SAFE: "var(--status-safe)",
  MONITOR: "var(--status-monitor)",
  FURTHER_TESTING: "var(--status-further)",
  CRITICAL: "var(--status-critical)",
};

export const formatDate = (d: Date) =>
  d
    .toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric" })
    .toUpperCase()
    .replace(/,/g, "");
