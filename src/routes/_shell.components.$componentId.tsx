import { Link, createFileRoute } from "@tanstack/react-router";
import { ArrowLeft, Check, Circle } from "lucide-react";
import { useAnalysisStore } from "@/store/analysisStore";
import { DriftChart } from "@/components/charts/DriftChart";
import { StatusBadge } from "@/components/analysis/StatusBadge";
import { PARAMETER_LABELS, STATUS_COLOR, withUnit } from "@/utils/formatters";
import { RECOMMENDATION, buildExplanation, buildFactors } from "@/utils/explainability";

export const Route = createFileRoute("/_shell/components/$componentId")({
  head: () => ({
    meta: [
      { title: "Component Analysis — Anomaly & Drift Detail | BurnIn-AI" },
      {
        name: "description",
        content:
          "Detailed burn-in behavior for a single component: anomaly detection, drift prediction, contributing factors and the final engineering recommendation.",
      },
      { property: "og:title", content: "Component Analysis — BurnIn-AI" },
      {
        property: "og:description",
        content: "Module A anomaly detection and Module B drift prediction for a single component.",
      },
    ],
  }),
  component: ComponentDetail,
});

function ComponentDetail() {
  const { componentId } = Route.useParams();
  const { results, settings } = useAnalysisStore();
  const a = results.find((r) => r.componentID === componentId);

  if (!a) {
    return (
      <div className="panel p-10 text-center">
        <p className="text-sm text-muted-foreground">
          No analysis found for <span className="font-mono">{componentId}</span>.
        </p>
        <Link to="/components" className="mt-4 inline-block font-mono text-xs text-primary hover:underline">
          BACK TO COMPONENTS
        </Link>
      </div>
    );
  }

  const explanation = buildExplanation(a);
  const factors = buildFactors(a);
  const rec = RECOMMENDATION[a.status];
  const ratio = a.lotAverage > 1e-9 ? a.currentValue / a.lotAverage : 1;
  const color = STATUS_COLOR[a.status];

  return (
    <div className="space-y-6 fade-up">
      <Link
        to="/components"
        className="inline-flex items-center gap-2 font-mono text-[11px] tracking-[0.12em] text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="h-3.5 w-3.5" aria-hidden /> BACK TO COMPONENTS
      </Link>

      <header className="panel flex flex-wrap items-center justify-between gap-6 p-6">
        <div>
          <h1 className="font-mono text-3xl font-semibold tracking-tight">{a.componentID}</h1>
          <p className="mt-2 font-mono text-xs text-muted-foreground">
            {a.lotID} · {PARAMETER_LABELS[a.parameter] ?? a.parameter}
          </p>
        </div>
        <div className="flex items-center gap-8">
          <StatusBadge status={a.status} size="lg" />
          <div>
            <div className="label-xs">RISK SCORE</div>
            <div className="font-mono text-4xl font-semibold tabular-nums" style={{ color }}>
              {a.riskScore}
              <span className="text-base text-muted-foreground"> / 100</span>
            </div>
            <div className="mt-2 h-1.5 w-52 overflow-hidden rounded bg-secondary">
              <div className="h-full" style={{ width: `${a.riskScore}%`, background: color }} />
            </div>
          </div>
          <div>
            <div className="label-xs">CONFIDENCE</div>
            <div className="font-mono text-xl tabular-nums">{(a.confidence * 100).toFixed(0)}%</div>
          </div>
        </div>
      </header>

      <section className="panel p-5">
        <h2 className="label-xs">PARAMETER BEHAVIOR OVER BURN-IN</h2>
        <DriftChart a={a} height={460} />
      </section>

      <section className="grid gap-5 xl:grid-cols-2">
        <div className="panel p-5">
          <div className="flex items-baseline gap-3">
            <span className="font-mono text-[11px] tracking-[0.16em] text-primary">MODULE A</span>
            <h2 className="text-lg font-semibold tracking-tight">ANOMALY DETECTION</h2>
          </div>
          <dl className="mt-4 grid gap-3 sm:grid-cols-2">
            <Metric k="LOT AVERAGE" v={withUnit(a.lotAverage, a.unit)} />
            <Metric k="COMPONENT" v={withUnit(a.currentValue, a.unit)} />
            <Metric k="DEVIATION" v={`${ratio.toFixed(1)}× LOT AVERAGE`} />
            <Metric k="LOT STD DEV" v={withUnit(a.lotStdDev, a.unit)} />
            <Metric k="Z-SCORE" v={`${a.zScore.toFixed(2)}σ`} strong />
            <Metric k="THRESHOLD" v={`${settings.zThreshold.toFixed(2)}σ`} />
          </dl>
          <Verdict
            ok={!a.anomalyFlag}
            text={a.anomalyFlag ? "ANOMALY DETECTED" : "NO STATISTICAL ANOMALY"}
          />
        </div>

        <div className="panel p-5">
          <div className="flex items-baseline gap-3">
            <span className="font-mono text-[11px] tracking-[0.16em] text-cyan">MODULE B</span>
            <h2 className="text-lg font-semibold tracking-tight">DRIFT PREDICTION</h2>
          </div>
          <dl className="mt-4 grid gap-3 sm:grid-cols-2">
            <Metric k="CURRENT" v={withUnit(a.currentValue, a.unit)} />
            <Metric k="PREDICTED 168h" v={withUnit(a.predicted_168h, a.unit)} strong />
            <Metric k="ACTUAL 168h" v={withUnit(a.value_168h, a.unit)} />
            <Metric
              k="PREDICTION ERROR"
              v={
                a.value_168h === null
                  ? "—"
                  : withUnit(Math.abs(a.predicted_168h - a.value_168h), a.unit)
              }
            />
            <Metric k="DRIFT RATE" v={`${a.driftRate.toFixed(3)} ${a.unit}/hr`} />
            <Metric k="SAFE SLOPE" v={`${a.safeSlope.toFixed(3)} ${a.unit}/hr`} />
          </dl>
          <Verdict
            ok={!a.driftFlag}
            text={a.driftFlag ? "DRIFT EXCEEDS SAFETY LIMIT" : "DRIFT WITHIN SAFETY LIMIT"}
          />
        </div>
      </section>

      <section className="panel grid gap-6 p-7 xl:grid-cols-[1.6fr_1fr]">
        <div>
          <h2 className="text-xl font-semibold tracking-tight">WHY WAS THIS COMPONENT FLAGGED?</h2>
          <div className="mt-4 space-y-4">
            {explanation.map((p) => (
              <p key={p} className="max-w-3xl text-sm leading-relaxed text-foreground/90">
                {p}
              </p>
            ))}
          </div>
        </div>
        <div>
          <h3 className="label-xs">CONTRIBUTING FACTORS</h3>
          <ul className="mt-3 space-y-2.5">
            {factors.map((f) => (
              <li key={f.label} className="flex items-start gap-2.5 text-sm">
                {f.active ? (
                  <Check className="mt-0.5 h-4 w-4 shrink-0 text-further" aria-hidden />
                ) : (
                  <Circle className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground/60" aria-hidden />
                )}
                <span className={f.active ? "text-foreground" : "text-muted-foreground"}>
                  {f.label}
                  <span className="sr-only">{f.active ? " — present" : " — not present"}</span>
                </span>
              </li>
            ))}
          </ul>
        </div>
      </section>

      <section className="panel border-l-2 p-6" style={{ borderLeftColor: color }}>
        <div className="label-xs">FINAL RECOMMENDATION</div>
        <h2 className="mt-2 text-2xl font-semibold tracking-tight" style={{ color }}>
          {rec.title}
        </h2>
        <p className="mt-2 max-w-3xl text-sm leading-relaxed text-muted-foreground">{rec.body}</p>
      </section>
    </div>
  );
}

function Metric({ k, v, strong }: { k: string; v: string; strong?: boolean }) {
  return (
    <div className="rounded-md border border-border bg-surface-2/40 px-3 py-2.5">
      <dt className="label-xs">{k}</dt>
      <dd
        className={`mt-1 font-mono tabular-nums ${strong ? "text-xl text-foreground" : "text-sm text-foreground/90"}`}
      >
        {v}
      </dd>
    </div>
  );
}

function Verdict({ ok, text }: { ok: boolean; text: string }) {
  return (
    <div
      className={`mt-4 rounded-md border px-4 py-3 font-mono text-sm tracking-[0.1em] ${
        ok ? "border-safe/40 bg-safe/10 text-safe" : "border-critical/40 bg-critical/10 text-critical"
      }`}
    >
      ● {text}
    </div>
  );
}
