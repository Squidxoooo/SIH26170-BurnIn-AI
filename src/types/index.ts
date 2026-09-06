export type Status = "SAFE" | "MONITOR" | "FURTHER_TESTING" | "CRITICAL";

export interface RawRow {
  componentID: string;
  lotID: string;
  parameter: string;
  value_0h: number | null;
  value_24h: number | null;
  value_96h: number | null;
  value_168h: number | null;
  datasheetMax: number;
}

export interface ComponentAnalysis {
  componentID: string;
  lotID: string;
  parameter: string;

  value_0h: number;
  value_24h: number;
  value_96h: number | null;
  value_168h: number | null;

  datasheetMax: number;
  safetyThreshold: number;

  predicted_168h: number;

  currentValue: number;
  lotAverage: number;
  lotStdDev: number;
  lotAvgSeries: { t: number; v: number }[];

  zScore: number;

  driftRate: number;
  safeSlope: number;

  anomalyFlag: boolean;
  driftFlag: boolean;
  exceedsDatasheet: boolean;

  riskScore: number;
  confidence: number;

  unit: string;
  status: Status;
}

export interface Settings {
  zThreshold: number;
  safeSlopes: Record<string, number>;
}

export interface ValidationReport {
  totalRows: number;
  validRows: number;
  errors: string[];
  warnings: string[];
}
