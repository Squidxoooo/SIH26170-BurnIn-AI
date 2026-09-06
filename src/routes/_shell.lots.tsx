import { useMemo } from "react";
import { createFileRoute } from "@tanstack/react-router";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { useAnalysisStore } from "@/store/analysisStore";

export const Route = createFileRoute("/_shell/lots")({
  head: () => ({
    meta: [
      { title: "Lot Comparison — Systemic Reliability Trends | BurnIn-AI" },
      {
        name: "description",
        content:
          "Compare anomaly concentration, parameter health and drift profiles across burn-in lots to separate isolated defects from systemic lot problems.",
      },
      { property: "og:title", content: "Lot Comparison — BurnIn-AI" },
      {
        property: "og:description",
        content: "Is this an isolated component problem or a systemic lot problem?",
      },
    ],
  }),
  component: LotComparison,
});

function LotComparison() {
  const { results } = useAnalysisStore();

  const lots = useMemo(() => {
    const map = new Map<string, typeof results>();
    results.forEach((r) => {
      if (!map.has(r.lotID)) map.set(r.lotID, []);
      map.get(r.lotID)!.push(r);
    });
    return [...map.entries()]
      .map(([lotID, items]) => ({
        lotID,
        total: items.length,
        anomalies: items.filter((i) => i.anomalyFlag).length,
        critical: items.filter((i) => i.status === "CRITICAL").length,
        passRate:
          (items.filter((i) => i.status === "SAFE" || i.status === "MONITOR").length /
            items.length) *
          100,
        avgRisk: items.reduce((a, b) => a + b.riskScore, 0) / items.length,
      }))
      .sort((a, b) => a.lotID.localeCompare(b.lotID));
  }, [results]);

  const paramHealth = useMemo(() => {
    const map = new Map<string, { parameter: string; anomalies: number; avgRisk: number; n: number }>();
    results.forEach((r) => {
      const e = map.get(r.parameter) ?? { parameter: r.parameter, anomalies: 0, avgRisk: 0, n: 0 };
      e.anomalies += r.anomalyFlag ? 1 : 0;
      e.avgRisk += r.riskScore;
      e.n += 1;
      map.set(r.parameter, e);
    });
    return [...map.values()].map((e) => ({
      parameter: e.parameter,
      anomalies: e.anomalies,
      avgRisk: Number((e.avgRisk / e.n).toFixed(1)),
    }));
  }, [results]);

  const driftProfile = useMemo(() => {
    const keys = ["value_0h", "value_24h", "value_96h", "value_168h"] as const;
    return [0, 24, 96, 168].map((t, idx) => {
      const point: Record<string, number> = { t };
      const key = keys[idx]!;
      lots.forEach((l) => {
        const items = results.filter((r) => r.lotID === l.lotID);
        const norm = items
          .map((i) => {
            const v = i[key];
            return v === null ? null : (v / i.datasheetMax) * 100;
          })
          .filter((v): v is number => v !== null);
        point[l.lotID] = norm.length
          ? Number((norm.reduce((a, b) => a + b, 0) / norm.length).toFixed(2))
          : 0;
      });
      return point;
    });
  }, [lots, results]);

  const colors = ["var(--primary)", "var(--cyan)", "var(--status-further)", "var(--status-safe)", "var(--status-monitor)"];
  const tooltip = {
    background: "var(--popover)",
    border: "1px solid var(--border)",
    borderRadius: 8,
    fontSize: 12,
  };

  return (
    <div className="space-y-6 fade-up">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight">LOT COMPARISON</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Is this an isolated component problem, or a systemic lot problem?
        </p>
      </div>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
        {lots.map((l) => (
          <div key={l.lotID} className="panel p-4">
            <div className="font-mono text-sm">{l.lotID}</div>
            <dl className="mt-3 space-y-1.5 font-mono text-xs">
              <Row k="COMPONENTS" v={String(l.total)} />
              <Row k="ANOMALIES" v={String(l.anomalies)} />
              <Row k="CRITICAL" v={String(l.critical)} />
              <Row k="PASS RATE" v={`${l.passRate.toFixed(1)}%`} />
            </dl>
            <div className="mt-3 h-1.5 overflow-hidden rounded bg-secondary">
              <div
                className="h-full bg-safe"
                style={{ width: `${l.passRate}%` }}
                aria-hidden
              />
            </div>
          </div>
        ))}
      </section>

      <section className="grid gap-5 xl:grid-cols-2">
        <div className="panel p-5">
          <h2 className="label-xs">ANOMALY CONCENTRATION BY LOT</h2>
          <div className="mt-4 h-[320px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={lots} margin={{ left: -18, right: 8, top: 8 }}>
                <CartesianGrid stroke="var(--border)" strokeDasharray="2 6" vertical={false} />
                <XAxis dataKey="lotID" tick={{ fontSize: 10, fontFamily: "var(--font-mono)" }} stroke="var(--muted-foreground)" tickLine={false} />
                <YAxis tick={{ fontSize: 11 }} stroke="var(--muted-foreground)" tickLine={false} axisLine={false} />
                <Tooltip contentStyle={tooltip} cursor={{ fill: "color-mix(in oklab, var(--primary) 10%, transparent)" }} />
                <Legend wrapperStyle={{ fontSize: 11 }} />
                <Bar dataKey="anomalies" name="Anomalies" fill="var(--status-further)" radius={[3, 3, 0, 0]} />
                <Bar dataKey="critical" name="Critical" fill="var(--status-critical)" radius={[3, 3, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="panel p-5">
          <h2 className="label-xs">PARAMETER HEALTH</h2>
          <div className="mt-4 h-[320px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={paramHealth} margin={{ left: -18, right: 8, top: 8 }}>
                <CartesianGrid stroke="var(--border)" strokeDasharray="2 6" vertical={false} />
                <XAxis dataKey="parameter" tick={{ fontSize: 10 }} stroke="var(--muted-foreground)" tickLine={false} />
                <YAxis tick={{ fontSize: 11 }} stroke="var(--muted-foreground)" tickLine={false} axisLine={false} />
                <Tooltip contentStyle={tooltip} cursor={{ fill: "color-mix(in oklab, var(--primary) 10%, transparent)" }} />
                <Legend wrapperStyle={{ fontSize: 11 }} />
                <Bar dataKey="anomalies" name="Anomalies" fill="var(--primary)" radius={[3, 3, 0, 0]} />
                <Bar dataKey="avgRisk" name="Avg risk score" fill="var(--cyan)" radius={[3, 3, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </section>

      <section className="panel p-5">
        <h2 className="label-xs">LOT DRIFT PROFILE — MEAN % OF DATASHEET MAXIMUM</h2>
        <div className="mt-4 h-[380px]">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={driftProfile} margin={{ left: -12, right: 24, top: 8 }}>
              <CartesianGrid stroke="var(--border)" strokeDasharray="2 6" vertical={false} />
              <XAxis
                dataKey="t"
                type="number"
                domain={[0, 168]}
                ticks={[0, 24, 96, 168]}
                tickFormatter={(v) => `${v}h`}
                stroke="var(--muted-foreground)"
                tick={{ fontSize: 11, fontFamily: "var(--font-mono)" }}
                tickLine={false}
              />
              <YAxis
                unit="%"
                stroke="var(--muted-foreground)"
                tick={{ fontSize: 11, fontFamily: "var(--font-mono)" }}
                tickLine={false}
                axisLine={false}
              />
              <Tooltip contentStyle={tooltip} labelFormatter={(v) => `Time: ${v}h`} />
              <Legend wrapperStyle={{ fontSize: 11 }} />
              {lots.map((l, i) => (
                <Line
                  key={l.lotID}
                  dataKey={l.lotID}
                  stroke={colors[i % colors.length]}
                  strokeWidth={2}
                  dot={{ r: 3 }}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>
      </section>
    </div>
  );
}

function Row({ k, v }: { k: string; v: string }) {
  return (
    <div className="flex justify-between">
      <dt className="text-muted-foreground">{k}</dt>
      <dd className="tabular-nums">{v}</dd>
    </div>
  );
}
