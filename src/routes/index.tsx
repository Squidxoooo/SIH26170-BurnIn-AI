import { Link, createFileRoute, useNavigate } from "@tanstack/react-router";
import { ArrowRight, Activity, Gauge, ShieldCheck } from "lucide-react";
import ScrollExpand from "@/components/reactbits/ScrollExpand";
import { useAnalysisStore } from "@/store/analysisStore";
import earth from "@/assets/earth-hero.jpg.asset.json";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "BurnIn-AI — Component Burn-In Anomaly & Drift Detection" },
      {
        name: "description",
        content:
          "Detect latent defects and predict dangerous component drift before deployment. AI-powered burn-in anomaly detection and 168h drift prediction for flight hardware.",
      },
      { property: "og:title", content: "BurnIn-AI — AI-Powered Component Burn-In Analysis" },
      {
        property: "og:description",
        content:
          "Detect latent defects and predict dangerous component drift before deployment.",
      },
    ],
  }),
  component: Hero,
});

function Hero() {
  const navigate = useNavigate();
  const loadSample = useAnalysisStore((s) => s.loadSample);

  const start = () => {
    loadSample();
    navigate({ to: "/overview" });
  };

  return (
    <div className="relative bg-background">
      <ScrollExpand
        src={earth.url}
        alt="Planet Earth seen from space"
        title="BurnIn-AI"
        scrollHint="scroll down"
        startWidth={46}
        startHeight={58}
        startRadius={28}
        mediaZoom={1.3}
        scrollDistance={1.2}
        holdDistance={0.4}
        smoothing={0.12}
        overlayScrim={0.55}
        useWindowScroll
      >
        <h2 className="max-w-3xl text-balance text-3xl font-semibold tracking-tight text-white sm:text-5xl">
          Detect latent defects. Predict dangerous drift. Before deployment.
        </h2>
        <p className="mt-4 max-w-xl font-mono text-[11px] tracking-[0.24em] text-cyan">
          AI-POWERED COMPONENT BURN-IN ANALYSIS
        </p>
        <div className="mt-8 flex flex-wrap items-center justify-center gap-4">
          <button
            onClick={start}
            className="glow-cta inline-flex items-center gap-2 rounded-md bg-primary px-6 py-3 text-sm font-medium tracking-[0.08em] text-primary-foreground transition hover:brightness-110 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            START ANALYSIS <ArrowRight className="h-4 w-4" aria-hidden />
          </button>
          <Link
            to="/analysis"
            className="rounded-md border border-white/25 bg-black/40 px-6 py-3 font-mono text-[11px] tracking-[0.16em] text-white backdrop-blur transition-colors hover:bg-black/60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            VIEW SAMPLE DATA
          </Link>
        </div>
      </ScrollExpand>

      <section className="relative mx-auto max-w-6xl px-6 py-20">
        <div className="grid w-full gap-4 text-left sm:grid-cols-3">
          <Card
            icon={Activity}
            title="MODULE A · ANOMALY DETECTION"
            body="Z-score comparison against lot peers surfaces components that pass the datasheet but behave abnormally."
          />
          <Card
            icon={Gauge}
            title="MODULE B · DRIFT PREDICTION"
            body="Early 0h and 24h measurements project 168h behavior against a parameter-specific safety slope."
          />
          <Card
            icon={ShieldCheck}
            title="RISK CLASSIFICATION"
            body="Every component receives an explainable status, risk score and engineering recommendation."
          />
        </div>

        <p className="mt-12 text-center font-mono text-[10px] tracking-[0.24em] text-muted-foreground">
          BURN-IN DATA → STATISTICAL ANALYSIS → ANOMALY DETECTION → DRIFT PREDICTION → ENGINEERING
          DECISION
        </p>
      </section>
    </div>
  );
}

function Card({
  icon: Icon,
  title,
  body,
}: {
  icon: typeof Activity;
  title: string;
  body: string;
}) {
  return (
    <div className="panel p-5">
      <Icon className="h-5 w-5 text-primary" aria-hidden />
      <h2 className="mt-3 font-mono text-[11px] tracking-[0.14em] text-foreground">{title}</h2>
      <p className="mt-2 text-xs leading-relaxed text-muted-foreground">{body}</p>
    </div>
  );
}
