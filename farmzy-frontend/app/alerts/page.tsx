"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { AlertBadge } from "@/components/alert-badge";
import { api } from "@/lib/api";
import { useFarmStore } from "@/store/farm-store";

export default function AlertsPage() {
  const farmId = useFarmStore((state) => state.selectedFarmId);
  const [filter, setFilter] = useState("all");

  const query = useQuery({ queryKey: ["alerts", farmId], queryFn: () => api.getAlerts(farmId, true) });

  const items = (query.data?.items ?? []).filter((item) => {
    if (filter === "all") return true;
    if (filter === "resolved") return item.is_resolved;
    return item.severity === filter && !item.is_resolved;
  });

  const criticalCount = (query.data?.items ?? []).filter((item) => item.severity === "critical" && !item.is_resolved).length;
  const warningCount = (query.data?.items ?? []).filter((item) => item.severity === "warning" && !item.is_resolved).length;

  return (
    <div className="space-y-4">
      <section className="rounded-xl border border-red-700/30 bg-red-950/20 p-3">
        <p className="text-sm text-red-200">Critical: {criticalCount} | Warning: {warningCount}</p>
      </section>

      <div className="flex flex-wrap gap-2">
        {["all", "critical", "warning", "info", "resolved"].map((value) => (
          <button
            key={value}
            className={`rounded-md border px-2 py-1 text-xs ${
              filter === value ? "border-farm-accent text-farm-accent" : "border-green-700/40 text-gray-300"
            }`}
            onClick={() => setFilter(value)}
          >
            {value}
          </button>
        ))}
      </div>

      <div className="space-y-2">
        {items.map((alert) => (
          <div key={alert.id} className="space-y-2 rounded-xl border border-green-700/30 bg-farm-surface/90 p-3">
            <AlertBadge alert={alert} />
            {!alert.is_resolved ? (
              <button
                className="rounded-md border border-green-700/40 px-2 py-1 text-xs"
                onClick={async () => {
                  await api.resolveAlert(farmId, alert.id);
                  query.refetch();
                }}
              >
                Resolve
              </button>
            ) : (
              <p className="text-xs text-gray-400">Resolved</p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
