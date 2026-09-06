import type { ComponentAnalysis, RawRow, Settings, Status } from "@/types";
import { unitFor } from "./formatters";

export const DEFAULT_SAFE_SLOPES: Record<string, number> = {
  Iddq: 0.08,
  LeakageCurrent: 0.1,
  PropDelay: 0.012,
  VthDrift: 0.05,
};

export const DEFAULT_SETTINGS: Settings = {
  zThreshold: 2.5,
  safeSlopes: { ...DEFAULT_SAFE_SLOPES },
};

export const TIME_POINTS = [0, 24, 96, 168];

export const mean = (xs: number[]) => (xs.length ? xs.reduce((a, b) => a + b, 0) / xs.length : 0);

export const stdDev = (xs: number[]) => {
  if (xs.length < 2) return 0;
  const m = mean(xs);
  return Math.sqrt(xs.reduce((a, b) => a + (b - m) ** 2, 0) / (xs.length - 1));
};

const clamp = (v: number, lo: number, hi: number) => Math.min(hi, Math.max(lo, v));

const groupKey = (r: RawRow) => `${r.lotID}::${r.parameter}`;

/** Full analytical pipeline: lot statistics -> anomaly -> drift -> risk classification. */
export function analyzeDataset(rows: RawRow[], settings: Settings): ComponentAnalysis[] {
  const groups = new Map<string, RawRow[]>();
  for (const r of rows) {
    const k = groupKey(r);
    if (!groups.has(k)) groups.set(k, []);
    groups.get(k)!.push(r);
  }

  const out: ComponentAnalysis[] = [];

  for (const [, members] of groups) {
    const current = (r: RawRow) => r.value_168h ?? r.value_96h ?? r.value_24h ?? r.value_0h ?? 0;
    const values = members.map(current);
    const lotAverage = mean(values);
    const lotSd = stdDev(values);

    const lotAvgSeries = TIME_POINTS.map((t) => {
      const key = `value_${t}h` as keyof RawRow;
      const vs = members.map((m) => m[key] as number | null).filter((v): v is number => v !== null);
      return { t, v: mean(vs) };
    });

    for (const r of members) {
      const v0 = r.value_0h ?? 0;
      const v24 = r.value_24h ?? v0;
      const safeSlope = settings.safeSlopes[r.parameter] ?? DEFAULT_SAFE_SLOPES[r.parameter] ?? 0.1;

      const driftRate = (v24 - v0) / 24;
      const predicted = v0 + driftRate * 168;
      const cur = current(r);

      const zScore = lotSd > 1e-9 ? (cur - lotAverage) / lotSd : 0;
      const safetyThreshold = r.datasheetMax * 0.8;

      const anomalyFlag = Math.abs(zScore) >= settings.zThreshold;
      const driftFlag = driftRate > safeSlope || predicted > safetyThreshold;
      const exceedsDatasheet = Math.max(cur, predicted) > r.datasheetMax;

      const zPart = clamp((Math.abs(zScore) / (settings.zThreshold * 2)) * 48, 0, 48);
      const slopePart = clamp((driftRate / (safeSlope || 1)) * 18, 0, 34);
      const predPart = predicted > r.datasheetMax ? 18 : predicted > safetyThreshold ? 10 : 0;
      const riskScore = Math.round(clamp(zPart + slopePart + predPart, 0, 100));

      const present = [r.value_0h, r.value_24h, r.value_96h, r.value_168h].filter(
        (v) => v !== null,
      ).length;
      const confidence = clamp(0.45 + present * 0.13 + (members.length > 20 ? 0.05 : 0), 0, 0.99);

      let status: Status = "SAFE";
      if ((anomalyFlag && driftFlag) || riskScore >= 75 || exceedsDatasheet) status = "CRITICAL";
      else if (anomalyFlag || riskScore >= 55) status = "FURTHER_TESTING";
      else if (riskScore >= 32 || Math.abs(zScore) >= settings.zThreshold * 0.7 || driftFlag)
        status = "MONITOR";

      out.push({
        componentID: r.componentID,
        lotID: r.lotID,
        parameter: r.parameter,
        value_0h: v0,
        value_24h: v24,
        value_96h: r.value_96h,
        value_168h: r.value_168h,
        datasheetMax: r.datasheetMax,
        safetyThreshold,
        predicted_168h: predicted,
        currentValue: cur,
        lotAverage,
        lotStdDev: lotSd,
        lotAvgSeries,
        zScore,
        driftRate,
        safeSlope,
        anomalyFlag,
        driftFlag,
        exceedsDatasheet,
        riskScore,
        confidence,
        unit: unitFor(r.parameter),
        status,
      });
    }
  }

  return out.sort((a, b) => a.componentID.localeCompare(b.componentID));
}

export interface DatasetSummary {
  total: number;
  safe: number;
  monitor: number;
  further: number;
  critical: number;
  anomalies: number;
  driftRisks: number;
  passRate: number;
}

export function summarize(items: ComponentAnalysis[]): DatasetSummary {
  const count = (s: Status) => items.filter((i) => i.status === s).length;
  const safe = count("SAFE");
  const monitor = count("MONITOR");
  return {
    total: items.length,
    safe,
    monitor,
    further: count("FURTHER_TESTING"),
    critical: count("CRITICAL"),
    anomalies: items.filter((i) => i.anomalyFlag).length,
    driftRisks: items.filter((i) => i.driftFlag).length,
    passRate: items.length ? ((safe + monitor) / items.length) * 100 : 0,
  };
}
