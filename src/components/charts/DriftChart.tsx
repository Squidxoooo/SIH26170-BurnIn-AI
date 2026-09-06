import { useMemo } from "react";
import {
  CartesianGrid,
  Line,
  ComposedChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  Legend,
} from "recharts";
import type { ComponentAnalysis } from "@/types";

interface Point {
  t: number;
  actual: number | null;
  predicted: number;
  lotAvg: number;
}

export function DriftChart({ a, height = 420 }: { a: ComponentAnalysis; height?: number }) {
  const data = useMemo<Point[]>(() => {
    const actual = [a.value_0h, a.value_24h, a.value_96h, a.value_168h];
    return [0, 24, 96, 168].map((t, i) => ({
      t,
      actual: actual[i] ?? null,
      predicted: a.value_0h + a.driftRate * t,
      lotAvg: a.lotAvgSeries[i]?.v ?? 0,
    }));
  }, [a]);

  const maxY = Math.max(
    a.datasheetMax,
    a.predicted_168h,
    ...data.map((d) => d.actual ?? 0),
  ) * 1.12;

  return (
    <div style={{ height }} aria-label="Burn-in drift analysis chart">
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={data} margin={{ top: 16, right: 24, bottom: 8, left: 4 }}>
          <CartesianGrid stroke="var(--border)" strokeDasharray="2 6" vertical={false} />
          <XAxis
            dataKey="t"
            type="number"
            domain={[0, 168]}
            ticks={[0, 24, 96, 168]}
            tickFormatter={(v) => `${v}h`}
            stroke="var(--muted-foreground)"
            tick={{ fontSize: 12, fontFamily: "var(--font-mono)" }}
            tickLine={false}
            axisLine={{ stroke: "var(--border)" }}
          />
          <YAxis
            domain={[0, Math.round(maxY)]}
            stroke="var(--muted-foreground)"
            tick={{ fontSize: 12, fontFamily: "var(--font-mono)" }}
            tickLine={false}
            axisLine={{ stroke: "var(--border)" }}
            label={{
              value: a.unit,
              angle: -90,
              position: "insideLeft",
              fill: "var(--muted-foreground)",
              fontSize: 11,
            }}
          />
          <Tooltip
            contentStyle={{
              background: "var(--popover)",
              border: "1px solid var(--border)",
              borderRadius: 8,
              fontSize: 12,
              fontFamily: "var(--font-mono)",
            }}
            labelFormatter={(v) => `Time: ${v}h`}
            formatter={(value: number | string, name) => [
              `${Number(value).toFixed(2)} ${a.unit}`,
              name,
            ]}
          />
          <Legend
            wrapperStyle={{ fontSize: 11, letterSpacing: "0.08em", textTransform: "uppercase" }}
          />
          <ReferenceLine
            y={a.datasheetMax}
            stroke="var(--muted-foreground)"
            strokeDasharray="4 4"
            label={{ value: "DATASHEET MAX", position: "right", fill: "var(--muted-foreground)", fontSize: 10 }}
          />
          <ReferenceLine
            y={a.safetyThreshold}
            stroke="var(--status-critical)"
            strokeDasharray="6 3"
            label={{ value: "SAFETY THRESHOLD", position: "insideTopRight", fill: "var(--status-critical)", fontSize: 10 }}
          />
          <Line
            name="Lot average"
            dataKey="lotAvg"
            stroke="var(--muted-foreground)"
            strokeDasharray="1 5"
            dot={false}
            strokeWidth={1.5}
            isAnimationActive={false}
          />
          <Line
            name="Predicted trajectory"
            dataKey="predicted"
            stroke="var(--cyan)"
            strokeDasharray="7 5"
            dot={false}
            strokeWidth={2}
          />
          <Line
            name="Actual measurement"
            dataKey="actual"
            stroke="var(--primary)"
            strokeWidth={2.5}
            dot={{ r: 4, fill: "var(--primary)", strokeWidth: 0 }}
            connectNulls
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
