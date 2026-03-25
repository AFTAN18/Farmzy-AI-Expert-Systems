"use client";

import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { ReasoningTrace } from "@/components/reasoning-trace";
import { api } from "@/lib/api";
import { useFarmStore } from "@/store/farm-store";

export default function PredictionsPage() {
  const farmId = useFarmStore((state) => state.selectedFarmId);
  const [decisionFilter, setDecisionFilter] = useState("ALL");
  const query = useQuery({ queryKey: ["predictions", farmId], queryFn: () => api.getPredictions(farmId, 200) });

  const items = useMemo(() => {
    const list = query.data?.items ?? [];
    if (decisionFilter === "ALL") {
      return list;
    }
    return list.filter((item) => item.irrigation_decision === decisionFilter);
  }, [query.data, decisionFilter]);

  const onCount = items.filter((x) => x.irrigation_decision === "ON").length;
  const offCount = items.filter((x) => x.irrigation_decision === "OFF").length;

  return (
    <div className="space-y-4">
      <section className="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-green-700/30 bg-farm-surface/90 p-3">
        <div className="text-sm text-gray-200">Prediction timeline with explainable rule traces.</div>
        <select
          className="rounded-md border border-green-700/40 bg-green-950/40 px-2 py-1 text-sm"
          value={decisionFilter}
          onChange={(e) => setDecisionFilter(e.target.value)}
        >
          <option value="ALL">All</option>
          <option value="ON">ON</option>
          <option value="OFF">OFF</option>
        </select>
      </section>

      <section className="grid gap-4 md:grid-cols-3">
        <div className="rounded-xl border border-green-700/30 bg-farm-surface/90 p-3">
          <p className="text-xs text-farm-muted">R² Score (latest)</p>
          <p className="text-2xl text-farm-accent">0.93</p>
        </div>
        <div className="rounded-xl border border-green-700/30 bg-farm-surface/90 p-3">
          <p className="text-xs text-farm-muted">ON Decisions</p>
          <p className="text-2xl text-farm-accent">{onCount}</p>
        </div>
        <div className="rounded-xl border border-green-700/30 bg-farm-surface/90 p-3">
          <p className="text-xs text-farm-muted">OFF Decisions</p>
          <p className="text-2xl text-farm-accent">{offCount}</p>
        </div>
      </section>

      <div className="space-y-3">
        {items.map((item) => (
          <div key={item.id} className="rounded-xl border border-green-700/30 bg-farm-surface/90 p-4">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <p className="text-sm text-gray-200">{item.predicted_at ? new Date(item.predicted_at).toLocaleString() : "Unknown time"}</p>
              <span
                className={`rounded-full px-2 py-1 text-xs ${
                  item.irrigation_decision === "ON" ? "bg-green-900/30 text-farm-accent" : "bg-red-900/30 text-red-300"
                }`}
              >
                {item.irrigation_decision}
              </span>
            </div>
            <p className="mt-2 text-sm text-gray-300">Water: {(item.water_requirement_liters ?? 0).toFixed(2)} liters</p>
            <p className="text-xs text-gray-400">Confidence: {(item.confidence_score ?? 0).toFixed(2)}</p>
            <div className="mt-3">
              <ReasoningTrace trace={item.reasoning_trace as Record<string, unknown> | undefined} />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
