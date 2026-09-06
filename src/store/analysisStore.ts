import { create } from "zustand";
import type { ComponentAnalysis, RawRow, Settings, ValidationReport } from "@/types";
import { DEFAULT_SETTINGS, analyzeDataset, summarize, type DatasetSummary } from "@/utils/calculations";
import { generateSampleRows } from "@/utils/mockData";

interface AnalysisState {
  rows: RawRow[];
  datasetName: string;
  settings: Settings;
  results: ComponentAnalysis[];
  summary: DatasetSummary;
  report: ValidationReport | null;
  loaded: boolean;

  loadSample: () => void;
  setDataset: (rows: RawRow[], name: string, report: ValidationReport) => void;
  setThreshold: (v: number) => void;
  setSafeSlope: (parameter: string, v: number) => void;
  clear: () => void;
}

const empty = summarize([]);

export const useAnalysisStore = create<AnalysisState>((set, get) => ({
  rows: [],
  datasetName: "—",
  settings: DEFAULT_SETTINGS,
  results: [],
  summary: empty,
  report: null,
  loaded: false,

  loadSample: () => {
    const rows = generateSampleRows();
    const results = analyzeDataset(rows, get().settings);
    set({
      rows,
      datasetName: "LOT_2026_001",
      results,
      summary: summarize(results),
      loaded: true,
      report: {
        totalRows: rows.length,
        validRows: rows.length,
        errors: [],
        warnings: [
          `Missing 96h/168h measurements for ${rows.filter((r) => r.value_168h === null).length} components. These components are excluded from drift validation.`,
        ],
      },
    });
  },

  setDataset: (rows, name, report) => {
    const results = analyzeDataset(rows, get().settings);
    set({ rows, datasetName: name, results, summary: summarize(results), report, loaded: true });
  },

  setThreshold: (v) => {
    const settings = { ...get().settings, zThreshold: v };
    const results = analyzeDataset(get().rows, settings);
    set({ settings, results, summary: summarize(results) });
  },

  setSafeSlope: (parameter, v) => {
    const settings = {
      ...get().settings,
      safeSlopes: { ...get().settings.safeSlopes, [parameter]: v },
    };
    const results = analyzeDataset(get().rows, settings);
    set({ settings, results, summary: summarize(results) });
  },

  clear: () =>
    set({ rows: [], results: [], summary: empty, datasetName: "—", loaded: false, report: null }),
}));
