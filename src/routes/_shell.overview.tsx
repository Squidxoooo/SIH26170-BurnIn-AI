import { useMemo } from "react";
import { Link, createFileRoute } from "@tanstack/react-router";
import {
  Bar,
  BarChart,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { ArrowRight, ArrowUpRight } from "lucide-react";
import { useAnalysisStore } from "@/store/analysisStore";
import { RiskBar, StatusBadge } from "@/components/analysis/StatusBadge";
import { DriftChart } from "@/components/charts/DriftChart";
import { STATUS_LABEL } from "@/utils/formatters";
import type { Status } from "@/types";

export const Route = createFileRoute("/_shell/overview")({
  head: () => ({
    meta: [
      { title: "Overview — BurnIn-AI Component Reliability" },
      {
        name: "description",
        content:
          "Burn-in analysis overview: component health distribution, anomalies, drift risks and pass rate for the active lot.",
      },
      { property: "og:title", content: "Overview — BurnIn-AI Component Reliability" },
      {
        property: "og:description",
        content: "Anomaly and drift health summary for the analyzed burn-in dataset.",
      },
    ],
  }),
  component: Overview,
});

const STATUS_ORDER: Status[] = ["SAFE", "MONITOR", "FURTHER_TESTING", "CRITICAL"];
const STATUS_VAR: Record<Status, string> = {
  SAFE: "var(--status-safe)",
  MONITOR: "var(--status-monitor)",
  FURTHER_TESTING: "var(--status-further)",
  CRITICAL: "var(--status-critical)",
};

function Overview() {
  const { results, summary, datasetName } = useAnalysisStore();

  const distribution = useMemo(
    () =>
      STATUS_ORDER.map((s) => ({
        status: s,
        name: STATUS_LABEL[s],
        value: results.filter((r) => r.status === s).length,
      })),
    [results],
  );

  const topRisk = useMemo(
    () => [...results].sort((a, b) => b.riskScore - a.riskScore).slice(0, 8),
    [results],
  );

  const featured = topRisk[0];

  return (
    <div className="space-y-7 fade-up">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight">BURN-IN ANALYSIS</h1>
          <p className="mt-1 text-sm text-muted-foreground">Component Reliability Overview</p>
          <p className="mt-2 font-mono text-xs text-muted-foreground">
            DATASET <span className="text-foreground">{datasetName}</span>
          </p>
        </div>
        <Link
          to="/analysis"
          className="glow-cta inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground transition hover:brightness-110 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        >
          ANALYZE NEW DATA <ArrowRight className="h-4 w-4" aria-hidden />
        </Link>
      </div>

      {/* Primary health summary */}
      <section className="panel grid gap-6 p-6 xl:grid-cols-[380px_1fr]">
        <div className="relative flex items-center justify-center">
          <ResponsiveContainer width="100%" height={280}>
            <PieChart>
              <Pie
                data={distribution}
                dataKey="value"
                nameKey="name"
                innerRadius={92}
                outerRadius={125}
                paddingAngle={2}
                stroke="none"
                isAnimationActive={false}
              >
                {distribution.map((d) => (
                  <Cell key={d.status} fill={STATUS_VAR[d.status]} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{
                  background: "var(--popover)",
                  border: "1px solid var(--border)",
                  borderRadius: 8,
                  fontSize: 12,
                }}
              />
            </PieChart>
          </ResponsiveContainer>
          <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
            <div className="font-mono text-5xl font-semibold tabular-nums text-foreground">
              {summary.passRate.toFixed(1)}%
            </div>
            <div className="label-xs mt-1">PASS RATE</div>
          </div>
        </div>

        <div className="flex flex-col justify-center gap-6">
          <div>
            <div className="label-xs">COMPONENTS ANALYZED</div>
            <div className="font-mono text-4xl font-semibold tabular-nums">{summary.total}</div>
          </div>
          <div className="grid gap-4 sm:grid-cols-3">
            <Stat label="CRITICAL" value={summary.critical} color="var(--status-critical)" />
            <Stat label="ANOMALIES" value={summary.anomalies} color="var(--status-further)" />
            <Stat label="DRIFT RISKS" value={summary.driftRisks} color="var(--status-monitor)" />
          </div>
          <div className="space-y-2">
            {distribution.map((d) => (
              <div key={d.status} className="flex items-center gap-3 text-xs">
                <span
                  className="h-2 w-2 rounded-sm"
                  style={{ background: STATUS_VAR[d.status] }}
                  aria-hidden
                />
                <span className="w-36 font-mono tracking-[0.1em] text-muted-foreground">
                  {d.name}
                </span>
                <div className="h-1.5 flex-1 overflow-hidden rounded bg-secondary">
                  <div
                    className="h-full"
                    style={{
                      width: `${summary.total ? (d.value / summary.total) * 100 : 0}%`,
                      background: STATUS_VAR[d.status],
                    }}
                  />
                </div>
                <span className="w-10 text-right font-mono tabular-nums">{d.value}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* KPI cards */}
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <Kpi
          label="COMPONENTS ANALYZED"
          value={String(summary.total)}
          context="Across all lots and parameters"
        />
        <Kpi
          label="ANOMALIES DETECTED"
          value={String(summary.anomalies)}
          context="Beyond configured Z-score threshold"
          accent="var(--status-further)"
        />
        <Kpi
          label="DRIFT RISKS"
          value={String(summary.driftRisks)}
          context="Predicted 168h above safety limit"
          accent="var(--status-monitor)"
        />
        <Kpi
          label="PASS RATE"
          value={`${summary.passRate.toFixed(1)}%`}
          context="Safe + monitor classifications"
          accent="var(--status-safe)"
        />
      </section>

      {/* Analytics */}
      <section className="grid gap-5 xl:grid-cols-2">
        <div className="panel p-5">
          <h2 className="label-xs">COMPONENT HEALTH DISTRIBUTION</h2>
          <div className="mt-4 h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={distribution} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
                <XAxis
                  dataKey="name"
                  stroke="var(--muted-foreground)"
                  tick={{ fontSize: 10 }}
                  tickLine={false}
                  axisLine={{ stroke: "var(--border)" }}
                />
                <YAxis
                  stroke="var(--muted-foreground)"
                  tick={{ fontSize: 11, fontFamily: "var(--font-mono)" }}
                  tickLine={false}
                  axisLine={false}
                />
                <Tooltip
                  cursor={{ fill: "color-mix(in oklab, var(--primary) 10%, transparent)" }}
                  contentStyle={{
                    background: "var(--popover)",
                    border: "1px solid var(--border)",
                    borderRadius: 8,
                    fontSize: 12,
                  }}
                />
                <Bar dataKey="value" name="Components" radius={[3, 3, 0, 0]} isAnimationActive={false}>
                  {distribution.map((d) => (
                    <Cell key={d.status} fill={STATUS_VAR[d.status]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="panel p-5">
          <div className="flex items-center justify-between">
            <h2 className="label-xs">HIGHEST RISK COMPONENTS</h2>
            <Link
              to="/components"
              className="inline-flex items-center gap-1 font-mono text-[11px] tracking-[0.12em] text-primary hover:underline"
            >
              VIEW CRITICAL COMPONENTS <ArrowUpRight className="h-3 w-3" aria-hidden />
            </Link>
          </div>
          <ol className="mt-3 divide-y divide-border">
            {topRisk.map((c, i) => (
              <li key={`${c.componentID}-${c.parameter}`}>
                <Link
                  to="/components/$componentId"
                  params={{ componentId: c.componentID }}
                  className="flex items-center gap-4 px-1 py-2.5 transition-colors hover:bg-accent/40 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                >
                  <span className="font-mono text-xs text-muted-foreground">
                    {String(i + 1).padStart(2, "0")}
                  </span>
                  <span className="min-w-0 flex-1">
                    <span className="block font-mono text-sm text-foreground">{c.componentID}</span>
                    <span className="block text-xs text-muted-foreground">{c.parameter}</span>
                  </span>
                  <StatusBadge status={c.status} />
                  <RiskBar score={c.riskScore} status={c.status} />
                </Link>
              </li>
            ))}
          </ol>
        </div>
      </section>

      {/* Main drift visualization */}
      {featured && (
        <section className="panel p-5">
          <div className="flex flex-wrap items-end justify-between gap-3">
            <div>
              <h2 className="text-lg font-semibold tracking-tight">BURN-IN DRIFT ANALYSIS</h2>
              <p className="mt-1 font-mono text-xs text-muted-foreground">
                {featured.componentID} · {featured.lotID} · {featured.parameter}
              </p>
            </div>
            <Link
              to="/components/$componentId"
              params={{ componentId: featured.componentID }}
              className="rounded-md border border-border px-3 py-1.5 font-mono text-[11px] tracking-[0.12em] hover:bg-accent"
            >
              OPEN DETAILED ANALYSIS
            </Link>
          </div>
          <DriftChart a={featured} height={440} />
        </section>
      )}
    </div>
  );
}

function Stat({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className="rounded-md border border-border bg-surface-2/40 px-4 py-3">
      <div className="font-mono text-2xl font-semibold tabular-nums" style={{ color }}>
        {value}
      </div>
      <div className="label-xs mt-1">{label}</div>
    </div>
  );
}

function Kpi({
  label,
  value,
  context,
  accent = "var(--muted-foreground)",
}: {
  label: string;
  value: string;
  context: string;
  accent?: string;
}) {
  return (
    <div className="panel p-5">
      <div className="flex items-start justify-between">
        <div className="label-xs">{label}</div>
        <span className="h-2 w-2 rounded-full" style={{ background: accent }} aria-hidden />
      </div>
      <div className="mt-3 font-mono text-3xl font-semibold tabular-nums">{value}</div>
      <p className="mt-2 text-xs text-muted-foreground">{context}</p>
    </div>
  );
}
