import type { RawRow } from "@/types";

/** Deterministic PRNG so the demo dataset is stable across reloads. */
function mulberry32(seed: number) {
  let a = seed;
  return () => {
    a |= 0;
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

const PARAMS = [
  { name: "Iddq", base: 9.5, spread: 1.4, max: 45, safe: 0.08 },
  { name: "LeakageCurrent", base: 10.2, spread: 1.8, max: 50, safe: 0.1 },
  { name: "PropDelay", base: 4.2, spread: 0.35, max: 8, safe: 0.012 },
  { name: "VthDrift", base: 12, spread: 2.2, max: 60, safe: 0.05 },
];

const LOTS = ["LOT_2026_001", "LOT_2026_002", "LOT_2026_003", "LOT_2026_004", "LOT_2026_005"];

const r2 = (v: number) => Math.round(v * 100) / 100;

export function generateSampleRows(): RawRow[] {
  const rand = mulberry32(20260906);
  const rows: RawRow[] = [];

  LOTS.forEach((lotID, li) => {
    const lotHealth = [1, 1.05, 1.35, 1, 1.15][li] ?? 1;
    for (let i = 1; i <= 50; i++) {
      const p = PARAMS[(i + li) % PARAMS.length]!;
      const suffix = ["A", "B", "C"][i % 3]!;
      const componentID = `COMP_${String(i + li * 50).padStart(3, "0")}_${suffix}`;

      const roll = rand();
      let profile: "normal" | "hidden" | "drift" | "critical" | "missing" = "normal";
      const anomalyChance = 0.1 * lotHealth;
      if (roll < 0.03) profile = "missing";
      else if (roll < 0.03 + anomalyChance) profile = "hidden";
      else if (roll < 0.03 + anomalyChance * 1.8) profile = "drift";
      else if (roll < 0.03 + anomalyChance * 2.2) profile = "critical";

      const v0 = p.base + (rand() - 0.5) * p.spread;
      let slope = p.safe * (0.08 + rand() * 0.32);
      let offset = 0;

      if (profile === "hidden") offset = p.base * (2.4 + rand() * 1.6);
      if (profile === "drift") slope = p.safe * (1.15 + rand() * 1.1);
      if (profile === "critical") {
        offset = p.base * (2.8 + rand() * 1.8);
        slope = p.safe * (1.3 + rand() * 1.4);
      }

      const noise = () => (rand() - 0.5) * p.spread * 0.25;
      const start = v0 + offset;
      const value_0h = r2(start);
      const value_24h = r2(start + slope * 24 + noise());
      const value_96h = r2(start + slope * 96 * (0.94 + rand() * 0.12) + noise());
      const value_168h = r2(start + slope * 168 * (0.9 + rand() * 0.18) + noise());

      rows.push({
        componentID,
        lotID,
        parameter: p.name,
        value_0h,
        value_24h,
        value_96h: profile === "missing" ? null : value_96h,
        value_168h: profile === "missing" ? null : value_168h,
        datasheetMax: p.max,
      });
    }
  });

  return rows;
}

export function rowsToCSV(rows: RawRow[]): string {
  const head =
    "ComponentID,LotID,Parameter,Value_0h,Value_24h,Value_96h,Value_168h,DatasheetMax";
  const body = rows
    .map((r) =>
      [
        r.componentID,
        r.lotID,
        r.parameter,
        r.value_0h ?? "",
        r.value_24h ?? "",
        r.value_96h ?? "",
        r.value_168h ?? "",
        r.datasheetMax,
      ].join(","),
    )
    .join("\n");
  return `${head}\n${body}`;
}
