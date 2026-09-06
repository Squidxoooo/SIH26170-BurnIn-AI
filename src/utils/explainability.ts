import type { ComponentAnalysis } from "@/types";
import { PARAMETER_LABELS } from "./formatters";

export interface Factor {
  label: string;
  active: boolean;
}

export function buildExplanation(a: ComponentAnalysis): string[] {
  const label = (PARAMETER_LABELS[a.parameter] ?? a.parameter).toLowerCase();
  const ratio = a.lotAverage > 1e-9 ? a.currentValue / a.lotAverage : 1;
  const out: string[] = [];

  if (Math.abs(a.zScore) >= 1) {
    out.push(
      `This component's ${label} is approximately ${ratio.toFixed(1)}× the average of components in lot ${a.lotID} (${a.zScore.toFixed(2)}σ from the lot mean). ${
        a.currentValue <= a.datasheetMax
          ? "Although the value remains below the datasheet maximum, its behavior is statistically abnormal compared with similar components."
          : "The measured value has also exceeded the datasheet maximum."
      }`,
    );
  } else {
    out.push(
      `This component's ${label} sits within normal statistical variation for lot ${a.lotID} (${a.zScore.toFixed(2)}σ from the lot mean of ${a.lotAverage.toFixed(2)} ${a.unit}).`,
    );
  }

  if (a.driftRate > a.safeSlope) {
    out.push(
      `Early burn-in measurements show a continued upward trend of ${a.driftRate.toFixed(3)} ${a.unit}/hr against a safe slope of ${a.safeSlope.toFixed(3)} ${a.unit}/hr. The predicted 168h value of ${a.predicted_168h.toFixed(2)} ${a.unit} ${
        a.predicted_168h > a.safetyThreshold ? "exceeds" : "approaches"
      } the defined safety threshold of ${a.safetyThreshold.toFixed(2)} ${a.unit}, indicating an elevated risk of future failure.`,
    );
  } else {
    out.push(
      `Early-stage drift is contained at ${a.driftRate.toFixed(3)} ${a.unit}/hr, below the safe slope of ${a.safeSlope.toFixed(3)} ${a.unit}/hr. The projected 168h value of ${a.predicted_168h.toFixed(2)} ${a.unit} remains ${a.predicted_168h > a.safetyThreshold ? "above" : "below"} the safety threshold.`,
    );
  }

  return out;
}

export function buildFactors(a: ComponentAnalysis): Factor[] {
  return [
    { label: "High deviation from lot average", active: a.anomalyFlag },
    { label: "Rapid early-stage increase", active: a.driftRate > a.safeSlope },
    { label: "Predicted 168h value above safety threshold", active: a.predicted_168h > a.safetyThreshold },
    { label: "Datasheet maximum exceeded", active: a.exceedsDatasheet },
    { label: "Incomplete measurement series", active: a.value_168h === null || a.value_96h === null },
  ];
}

export const RECOMMENDATION: Record<
  ComponentAnalysis["status"],
  { title: string; body: string }
> = {
  SAFE: {
    title: "PASS",
    body: "Component behavior is within expected lot variation and predicted drift remains below the safety threshold.",
  },
  MONITOR: {
    title: "MONITOR",
    body: "Component shows some deviation but current evidence does not indicate an immediate safety concern. Continue routine burn-in monitoring.",
  },
  FURTHER_TESTING: {
    title: "FURTHER TESTING RECOMMENDED",
    body: "Component exhibits abnormal behavior relative to its lot and should undergo additional investigation before flight qualification.",
  },
  CRITICAL: {
    title: "REJECT / CRITICAL",
    body: "Component exhibits significant abnormal behavior and dangerous predicted drift. Rejection or further engineering review is recommended.",
  },
};
