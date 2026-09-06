import { useMemo, useState } from "react";
import { Link, createFileRoute } from "@tanstack/react-router";
import { Search } from "lucide-react";
import { useAnalysisStore } from "@/store/analysisStore";
import { RiskBar, StatusBadge } from "@/components/analysis/StatusBadge";
import { STATUS_LABEL, num } from "@/utils/formatters";
import type { Status } from "@/types";

export const Route = createFileRoute("/_shell/components/")({
  head: () => ({
    meta: [
      { title: "Components — Burn-In Anomaly Table | BurnIn-AI" },
      {
        name: "description",
        content:
          "Search, filter and sort every analyzed component by Z-score, drift rate, risk score and reliability status.",
      },
      { property: "og:title", content: "Components — Burn-In Anomaly Table" },
      {
        property: "og:description",
        content: "Full component-level anomaly and drift results with filtering and sorting.",
      },
    ],
  }),
  component: ComponentsPage,
});

type SortKey = "riskScore" | "zScore" | "driftRate" | "componentID";

function ComponentsPage() {
  const { results } = useAnalysisStore();
  const [q, setQ] = useState("");
  const [lot, setLot] = useState("ALL");
  const [param, setParam] = useState("ALL");
  const [status, setStatus] = useState("ALL");
  const [sort, setSort] = useState<SortKey>("riskScore");

  const lots = useMemo(() => [...new Set(results.map((r) => r.lotID))].sort(), [results]);
  const params = useMemo(() => [...new Set(results.map((r) => r.parameter))].sort(), [results]);

  const rows = useMemo(() => {
    const f = results.filter(
      (r) =>
        (lot === "ALL" || r.lotID === lot) &&
        (param === "ALL" || r.parameter === param) &&
        (status === "ALL" || r.status === status) &&
        r.componentID.toLowerCase().includes(q.toLowerCase()),
    );
    return f.sort((a, b) =>
      sort === "componentID"
        ? a.componentID.localeCompare(b.componentID)
        : sort === "zScore"
          ? Math.abs(b.zScore) - Math.abs(a.zScore)
          : (b[sort] as number) - (a[sort] as number),
    );
  }, [results, lot, param, status, q, sort]);

  return (
    <div className="space-y-5 fade-up">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight">COMPONENTS</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          {rows.length} of {results.length} components match the current filters.
        </p>
      </div>

      <div className="panel flex flex-wrap items-center gap-3 p-4">
        <div className="relative min-w-56 flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" aria-hidden />
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Search Component ID"
            aria-label="Search Component ID"
            className="w-full rounded-md border border-input bg-background py-2 pl-9 pr-3 font-mono text-xs focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          />
        </div>
        <Select label="Lot" value={lot} onChange={setLot} options={["ALL", ...lots]} />
        <Select label="Parameter" value={param} onChange={setParam} options={["ALL", ...params]} />
        <Select
          label="Status"
          value={status}
          onChange={setStatus}
          options={["ALL", "SAFE", "MONITOR", "FURTHER_TESTING", "CRITICAL"]}
          render={(o) => (o === "ALL" ? "ALL" : STATUS_LABEL[o as Status])}
        />
        <Select
          label="Sort"
          value={sort}
          onChange={(v) => setSort(v as SortKey)}
          options={["riskScore", "zScore", "driftRate", "componentID"]}
          render={(o) =>
            ({ riskScore: "RISK SCORE", zScore: "Z-SCORE", driftRate: "DRIFT RATE", componentID: "COMPONENT ID" })[o] ?? o
          }
        />
      </div>

      <div className="panel overflow-x-auto">
        <table className="w-full min-w-[1180px] text-left text-sm">
          <caption className="sr-only">Component burn-in analysis results</caption>
          <thead>
            <tr className="label-xs border-b border-border">
              {["Component", "Lot", "Parameter", "0h", "24h", "Predicted 168h", "Actual 168h", "Z-Score", "Drift Rate", "Status", "Risk"].map(
                (h) => (
                  <th key={h} scope="col" className="px-3 py-3 font-medium">
                    {h}
                  </th>
                ),
              )}
            </tr>
          </thead>
          <tbody>
            {rows.slice(0, 300).map((r) => (
              <tr key={`${r.componentID}-${r.parameter}`} className="border-b border-border/50 transition-colors hover:bg-accent/40">
                <td className="px-3 py-2.5">
                  <Link
                    to="/components/$componentId"
                    params={{ componentId: r.componentID }}
                    className="font-mono text-xs text-foreground hover:text-primary hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                  >
                    {r.componentID}
                  </Link>
                </td>
                <td className="px-3 py-2.5 font-mono text-xs text-muted-foreground">{r.lotID}</td>
                <td className="px-3 py-2.5 text-xs text-muted-foreground">{r.parameter}</td>
                <td className="px-3 py-2.5 font-mono text-xs tabular-nums">{num(r.value_0h)}</td>
                <td className="px-3 py-2.5 font-mono text-xs tabular-nums">{num(r.value_24h)}</td>
                <td className="px-3 py-2.5 font-mono text-xs tabular-nums text-cyan">{num(r.predicted_168h)}</td>
                <td className="px-3 py-2.5 font-mono text-xs tabular-nums">{num(r.value_168h)}</td>
                <td className="px-3 py-2.5 font-mono text-xs tabular-nums">{num(r.zScore)}σ</td>
                <td className="px-3 py-2.5 font-mono text-xs tabular-nums">{num(r.driftRate, 3)}</td>
                <td className="px-3 py-2.5"><StatusBadge status={r.status} /></td>
                <td className="px-3 py-2.5"><RiskBar score={r.riskScore} status={r.status} /></td>
              </tr>
            ))}
          </tbody>
        </table>
        {!rows.length && (
          <p className="p-8 text-center text-sm text-muted-foreground">
            No components match the current filters.
          </p>
        )}
      </div>
    </div>
  );
}

function Select({
  label,
  value,
  onChange,
  options,
  render,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  options: string[];
  render?: (o: string) => string;
}) {
  return (
    <label className="flex items-center gap-2">
      <span className="label-xs">{label}</span>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="rounded-md border border-input bg-background px-2 py-1.5 font-mono text-xs focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
      >
        {options.map((o) => (
          <option key={o} value={o}>
            {render ? render(o) : o}
          </option>
        ))}
      </select>
    </label>
  );
}
