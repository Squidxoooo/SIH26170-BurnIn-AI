import { useCallback, useRef, useState } from "react";
import { createFileRoute, useNavigate } from "@tanstack/react-router";
import Papa from "papaparse";
import { AlertTriangle, ArrowRight, CheckCircle2, FileUp, UploadCloud } from "lucide-react";
import { useAnalysisStore } from "@/store/analysisStore";
import type { RawRow, ValidationReport } from "@/types";

export const Route = createFileRoute("/_shell/analysis")({
  head: () => ({
    meta: [
      { title: "Analysis Workspace — Upload Burn-In Data | BurnIn-AI" },
      {
        name: "description",
        content:
          "Upload burn-in CSV measurements at 0h, 24h, 96h and 168h, validate the dataset and run anomaly and drift analysis.",
      },
      { property: "og:title", content: "Analysis Workspace — BurnIn-AI" },
      {
        property: "og:description",
        content: "Drop burn-in CSV data and run the anomaly and drift detection engine.",
      },
    ],
  }),
  component: AnalysisPage,
});

const REQUIRED = [
  "ComponentID",
  "LotID",
  "Parameter",
  "Value_0h",
  "Value_24h",
  "Value_96h",
  "Value_168h",
  "DatasheetMax",
];

const STAGES = [
  "Validating dataset",
  "Calculating lot statistics",
  "Detecting anomalies",
  "Predicting component drift",
  "Generating risk classifications",
];

const numOrNull = (v: string | undefined) => {
  if (v === undefined || v.trim() === "") return null;
  const n = Number(v);
  return Number.isFinite(n) ? n : null;
};

function AnalysisPage() {
  const navigate = useNavigate();
  const { setDataset, loadSample } = useAnalysisStore();
  const inputRef = useRef<HTMLInputElement>(null);

  const [dragging, setDragging] = useState(false);
  const [pending, setPending] = useState<{ rows: RawRow[]; report: ValidationReport; name: string } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState<number | null>(null);
  const [stage, setStage] = useState(0);

  const handleFile = useCallback((file: File) => {
    setError(null);
    setPending(null);
    if (!file.name.toLowerCase().endsWith(".csv")) {
      setError("Unsupported file type. Please provide a .csv file.");
      return;
    }
    if (file.size > 50 * 1024 * 1024) {
      setError("File exceeds the 50MB maximum.");
      return;
    }

    Papa.parse<Record<string, string>>(file, {
      header: true,
      skipEmptyLines: true,
      complete: (res) => {
        const fields = res.meta.fields ?? [];
        const missing = REQUIRED.filter((c) => !fields.includes(c));
        if (missing.length) {
          setError(`Missing required column(s): ${missing.join(", ")}`);
          return;
        }

        const rows: RawRow[] = [];
        const errors: string[] = [];
        let missing168 = 0;

        res.data.forEach((r, i) => {
          const id = (r["ComponentID"] ?? "").trim();
          const max = numOrNull(r["DatasheetMax"]);
          const v0 = numOrNull(r["Value_0h"]);
          const v24 = numOrNull(r["Value_24h"]);
          if (!id || max === null || v0 === null || v24 === null) {
            errors.push(`Row ${i + 2}: invalid or missing required numeric values — excluded.`);
            return;
          }
          const v168 = numOrNull(r["Value_168h"]);
          if (v168 === null) missing168++;
          rows.push({
            componentID: id,
            lotID: (r["LotID"] ?? "UNKNOWN").trim(),
            parameter: (r["Parameter"] ?? "UNKNOWN").trim(),
            value_0h: v0,
            value_24h: v24,
            value_96h: numOrNull(r["Value_96h"]),
            value_168h: v168,
            datasheetMax: max,
          });
        });

        if (!rows.length) {
          setError("No valid rows found in this file.");
          return;
        }

        const warnings: string[] = [];
        if (missing168)
          warnings.push(
            `Missing Value_168h for ${missing168} components. These components will be excluded from drift validation.`,
          );

        setPending({
          rows,
          name: rows[0]?.lotID ?? file.name,
          report: {
            totalRows: res.data.length,
            validRows: rows.length,
            errors: errors.slice(0, 8),
            warnings,
          },
        });
      },
      error: () => setError("The file could not be parsed. Please check the CSV format."),
    });
  }, []);

  const runAnalysis = () => {
    if (!pending) return;
    setProgress(0);
    setStage(0);
    let p = 0;
    const timer = setInterval(() => {
      p += 7 + Math.random() * 9;
      setStage(Math.min(STAGES.length - 1, Math.floor((p / 100) * STAGES.length)));
      if (p >= 100) {
        clearInterval(timer);
        setProgress(100);
        setDataset(pending.rows, pending.name, pending.report);
        setTimeout(() => navigate({ to: "/overview" }), 350);
      } else {
        setProgress(p);
      }
    }, 130);
  };

  if (progress !== null) {
    const done = Math.round((progress / 100) * pending!.rows.length);
    return (
      <div className="flex min-h-[70vh] items-center justify-center fade-up">
        <div className="panel w-full max-w-xl p-8">
          <h1 className="text-xl font-semibold tracking-tight">ANALYZING BURN-IN DATA</h1>
          <div className="mt-6 h-2 overflow-hidden rounded bg-secondary">
            <div
              className="h-full bg-primary transition-all duration-150"
              style={{ width: `${progress}%` }}
            />
          </div>
          <div className="mt-2 flex justify-between font-mono text-xs text-muted-foreground">
            <span>Processing {done} / {pending!.rows.length} components</span>
            <span className="tabular-nums text-foreground">{Math.round(progress)}%</span>
          </div>
          <ul className="mt-6 space-y-2 font-mono text-xs">
            {STAGES.map((s, i) => (
              <li
                key={s}
                className={
                  i < stage ? "text-safe" : i === stage ? "text-primary" : "text-muted-foreground"
                }
              >
                {i < stage ? "✓" : i === stage ? "●" : "○"} {s}
              </li>
            ))}
          </ul>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 fade-up">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight">ANALYSIS WORKSPACE</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Upload burn-in measurements to run anomaly detection and drift prediction.
        </p>
      </div>

      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragging(false);
          const f = e.dataTransfer.files?.[0];
          if (f) handleFile(f);
        }}
        className={`grid-bg panel flex flex-col items-center justify-center gap-3 p-16 text-center transition-colors ${
          dragging ? "border-primary bg-primary/5" : ""
        }`}
      >
        <UploadCloud className="h-10 w-10 text-primary" aria-hidden />
        <div className="text-lg font-semibold tracking-tight">DROP BURN-IN DATA HERE</div>
        <div className="font-mono text-xs text-muted-foreground">CSV FILE · MAXIMUM 50MB</div>
        <input
          ref={inputRef}
          type="file"
          accept=".csv,text/csv"
          className="sr-only"
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f) handleFile(f);
          }}
        />
        <div className="mt-3 flex flex-wrap justify-center gap-3">
          <button
            onClick={() => inputRef.current?.click()}
            className="glow-cta inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:brightness-110 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            <FileUp className="h-4 w-4" aria-hidden /> BROWSE FILE
          </button>
          <button
            onClick={() => {
              loadSample();
              navigate({ to: "/overview" });
            }}
            className="rounded-md border border-border px-4 py-2 font-mono text-[11px] tracking-[0.12em] hover:bg-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            USE SAMPLE DATASET
          </button>
        </div>
        <p className="mt-4 max-w-2xl font-mono text-[11px] leading-relaxed text-muted-foreground">
          REQUIRED COLUMNS: {REQUIRED.join(" · ")}
        </p>
      </div>

      {error && (
        <div className="flex items-start gap-3 rounded-md border border-critical/40 bg-critical/10 p-4 text-sm text-critical">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden />
          <span>{error}</span>
        </div>
      )}

      {pending && (
        <section className="panel p-5">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <h2 className="label-xs">DATASET PREVIEW</h2>
            <span className="font-mono text-xs text-muted-foreground">
              {pending.report.validRows} / {pending.report.totalRows} ROWS VALID
            </span>
          </div>

          {pending.report.warnings.map((w) => (
            <p
              key={w}
              className="mt-3 flex items-start gap-2 rounded border border-monitor/40 bg-monitor/10 p-3 text-xs text-monitor"
            >
              <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0" aria-hidden /> {w}
            </p>
          ))}
          {pending.report.errors.map((w) => (
            <p key={w} className="mt-2 font-mono text-[11px] text-muted-foreground">
              {w}
            </p>
          ))}

          <div className="mt-4 overflow-x-auto">
            <table className="w-full min-w-[820px] text-left text-xs">
              <thead className="label-xs border-b border-border">
                <tr>
                  {["Component", "Lot", "Parameter", "0h", "24h", "96h", "168h", "Max"].map((h) => (
                    <th key={h} className="px-2 py-2 font-medium">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="font-mono">
                {pending.rows.slice(0, 8).map((r, i) => (
                  <tr key={`${r.componentID}-${i}`} className="border-b border-border/60">
                    <td className="px-2 py-2">{r.componentID}</td>
                    <td className="px-2 py-2 text-muted-foreground">{r.lotID}</td>
                    <td className="px-2 py-2 text-muted-foreground">{r.parameter}</td>
                    <td className="px-2 py-2 tabular-nums">{r.value_0h ?? "—"}</td>
                    <td className="px-2 py-2 tabular-nums">{r.value_24h ?? "—"}</td>
                    <td className="px-2 py-2 tabular-nums">{r.value_96h ?? "—"}</td>
                    <td className="px-2 py-2 tabular-nums">{r.value_168h ?? "—"}</td>
                    <td className="px-2 py-2 tabular-nums text-muted-foreground">{r.datasheetMax}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="mt-5 flex items-center gap-3">
            <button
              onClick={runAnalysis}
              className="glow-cta inline-flex items-center gap-2 rounded-md bg-primary px-5 py-2.5 text-sm font-medium text-primary-foreground hover:brightness-110 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              ANALYZE COMPONENTS <ArrowRight className="h-4 w-4" aria-hidden />
            </button>
            <span className="inline-flex items-center gap-1.5 font-mono text-[11px] text-safe">
              <CheckCircle2 className="h-3.5 w-3.5" aria-hidden /> SCHEMA VALIDATED
            </span>
          </div>
        </section>
      )}
    </div>
  );
}
