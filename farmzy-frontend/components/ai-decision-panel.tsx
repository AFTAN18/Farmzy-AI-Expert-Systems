"use client";

import { ReasoningTrace } from "@/components/reasoning-trace";
import type { IrrigationPrediction } from "@/lib/types";

type AiDecisionPanelProps = {
  prediction: IrrigationPrediction | null;
};

export function AiDecisionPanel({ prediction }: AiDecisionPanelProps) {
  const decision = prediction?.irrigation_decision ?? "OFF";
  const liters = prediction?.water_requirement_liters ?? 0;
  const fuzzy = prediction?.fuzzy_membership_score ?? 0;

  return (
    <section className="rounded-xl border border-green-700/30 bg-farm-surface/90 p-5 shadow-glow">
      <p className="text-xs uppercase tracking-[0.2em] text-farm-muted">AI Decision</p>
      <h2 className={`mt-2 text-4xl font-bold ${decision === "ON" ? "text-farm-accent" : "text-red-400"}`}>
        IRRIGATION: {decision}
      </h2>
      <p className="mt-1 text-lg text-gray-200">Water requirement: {liters.toFixed(2)} Liters</p>

      <div className="mt-4">
        <p className="mb-1 text-xs uppercase tracking-[0.2em] text-farm-muted">Fuzzy Logic Score</p>
        <div className="h-2 rounded-full bg-green-950/60">
          <div className="h-full rounded-full bg-farm-accent" style={{ width: `${Math.min(100, Math.max(0, fuzzy * 100))}%` }} />
        </div>
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        {(prediction?.rules_fired ?? prediction?.expert_rule_fired?.split(",") ?? []).map((rule) => (
          <span key={rule} className="rounded-full border border-green-500/40 bg-green-900/30 px-2 py-1 text-xs text-farm-accent">
            {rule}
          </span>
        ))}
      </div>

      <div className="mt-4">
        <ReasoningTrace trace={prediction?.reasoning_trace as Record<string, unknown> | undefined} />
      </div>
    </section>
  );
}
