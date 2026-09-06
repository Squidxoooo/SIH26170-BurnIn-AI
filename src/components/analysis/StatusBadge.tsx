import { AlertTriangle, CheckCircle2, Eye, OctagonAlert } from "lucide-react";
import type { Status } from "@/types";
import { STATUS_LABEL } from "@/utils/formatters";

const MAP: Record<Status, { cls: string; Icon: typeof CheckCircle2 }> = {
  SAFE: { cls: "text-safe border-safe/40 bg-safe/10", Icon: CheckCircle2 },
  MONITOR: { cls: "text-monitor border-monitor/40 bg-monitor/10", Icon: Eye },
  FURTHER_TESTING: { cls: "text-further border-further/40 bg-further/10", Icon: AlertTriangle },
  CRITICAL: { cls: "text-critical border-critical/40 bg-critical/10", Icon: OctagonAlert },
};

export function StatusBadge({ status, size = "sm" }: { status: Status; size?: "sm" | "lg" }) {
  const { cls, Icon } = MAP[status];
  return (
    <span
      className={`inline-flex items-center gap-1.5 whitespace-nowrap rounded border font-mono font-medium tracking-[0.1em] ${cls} ${
        size === "lg" ? "px-3 py-1.5 text-xs" : "px-2 py-0.5 text-[10px]"
      }`}
    >
      <Icon className={size === "lg" ? "h-4 w-4" : "h-3 w-3"} aria-hidden />
      {STATUS_LABEL[status]}
    </span>
  );
}

export function RiskBar({ score, status }: { score: number; status: Status }) {
  const color = {
    SAFE: "var(--status-safe)",
    MONITOR: "var(--status-monitor)",
    FURTHER_TESTING: "var(--status-further)",
    CRITICAL: "var(--status-critical)",
  }[status];
  return (
    <div className="flex items-center gap-2">
      <div
        className="h-1.5 w-20 overflow-hidden rounded-full bg-secondary"
        role="meter"
        aria-valuenow={score}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label="Risk score"
      >
        <div className="h-full rounded-full" style={{ width: `${score}%`, background: color }} />
      </div>
      <span className="font-mono text-xs tabular-nums text-foreground">{score}</span>
    </div>
  );
}
