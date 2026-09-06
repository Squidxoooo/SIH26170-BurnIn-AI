import { createFileRoute } from "@tanstack/react-router";
import { toast } from "sonner";
import { useAnalysisStore } from "@/store/analysisStore";
import { DEFAULT_SAFE_SLOPES } from "@/utils/calculations";
import { rowsToCSV } from "@/utils/mockData";
import { PARAMETER_UNITS } from "@/utils/formatters";

export const Route = createFileRoute("/_shell/settings")({
  head: () => ({
    meta: [
      { title: "Settings — BurnIn-AI Analysis Engine" },
      {
        name: "description",
        content:
          "Configure the anomaly Z-score threshold, per-parameter safe slopes, dataset loading and analysis exports.",
      },
      { property: "og:title", content: "Settings — BurnIn-AI Analysis Engine" },
      {
        property: "og:description",
        content: "Anomaly threshold, safety slope and dataset export configuration.",
      },
    ],
  }),
  component: SettingsPage,
});

function download(name: string, content: string, type: string) {
  const url = URL.createObjectURL(new Blob([content], { type }));
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  a.click();
  URL.revokeObjectURL(url);
}

function SettingsPage() {
  const { settings, setThreshold, setSafeSlope, loadSample, clear, rows, results } =
    useAnalysisStore();

  return (
    <div className="max-w-4xl space-y-6 fade-up">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight">SETTINGS</h1>
        <p className="mt-1 text-sm text-muted-foreground">Analysis engine configuration</p>
      </div>

      <section className="panel space-y-4 p-5">
        <div>
          <h2 className="label-xs">ANOMALY THRESHOLD</h2>
          <p className="mt-1 text-xs text-muted-foreground">
            Components deviating beyond this many standard deviations from their lot mean are
            flagged as anomalies.
          </p>
        </div>
        <div className="flex items-center gap-5">
          <input
            type="range"
            min={1}
            max={5}
            step={0.1}
            value={settings.zThreshold}
            onChange={(e) => setThreshold(Number(e.target.value))}
            className="h-1.5 w-full max-w-md accent-[var(--primary)]"
            aria-label="Anomaly Z-score threshold"
          />
          <span className="font-mono text-2xl tabular-nums">
            {settings.zThreshold.toFixed(2)}σ
          </span>
        </div>
      </section>

      <section className="panel space-y-4 p-5">
        <div>
          <h2 className="label-xs">SAFETY SLOPE</h2>
          <p className="mt-1 text-xs text-muted-foreground">
            Maximum acceptable drift rate per parameter, in units per hour.
          </p>
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          {Object.keys(DEFAULT_SAFE_SLOPES).map((p) => (
            <label key={p} className="flex items-center justify-between gap-3 rounded-md border border-border px-3 py-2.5">
              <span className="font-mono text-xs">{p}</span>
              <span className="flex items-center gap-2">
                <input
                  type="number"
                  step={0.001}
                  min={0}
                  value={settings.safeSlopes[p] ?? 0}
                  onChange={(e) => setSafeSlope(p, Number(e.target.value))}
                  className="w-24 rounded border border-input bg-background px-2 py-1 text-right font-mono text-xs focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                />
                <span className="font-mono text-[10px] text-muted-foreground">
                  {PARAMETER_UNITS[p]}/hr
                </span>
              </span>
            </label>
          ))}
        </div>
      </section>

      <section className="panel space-y-3 p-5">
        <h2 className="label-xs">DATASET</h2>
        <div className="flex flex-wrap gap-3">
          <Btn onClick={() => { loadSample(); toast.success("Sample dataset loaded"); }}>
            LOAD SAMPLE DATASET
          </Btn>
          <Btn onClick={() => { clear(); toast("Analysis cleared"); }}>CLEAR ANALYSIS</Btn>
        </div>
      </section>

      <section className="panel space-y-3 p-5">
        <h2 className="label-xs">EXPORT</h2>
        <div className="flex flex-wrap gap-3">
          <Btn onClick={() => download("burnin-dataset.csv", rowsToCSV(rows), "text/csv")}>
            EXPORT CSV
          </Btn>
          <Btn
            onClick={() =>
              download("burnin-analysis.json", JSON.stringify(results, null, 2), "application/json")
            }
          >
            EXPORT JSON
          </Btn>
        </div>
      </section>
    </div>
  );
}

function Btn({ children, onClick }: { children: React.ReactNode; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className="rounded-md border border-border bg-surface-2/50 px-4 py-2 font-mono text-[11px] tracking-[0.12em] transition-colors hover:bg-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
    >
      {children}
    </button>
  );
}
