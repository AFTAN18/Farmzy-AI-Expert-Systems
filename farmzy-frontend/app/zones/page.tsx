"use client";

import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";

import { ScatterPca } from "@/components/scatter-pca";
import { ZoneCard } from "@/components/zone-card";
import { api } from "@/lib/api";
import { useFarmStore } from "@/store/farm-store";

export default function ZonesPage() {
  const farmId = useFarmStore((state) => state.selectedFarmId);
  const query = useQuery({ queryKey: ["zones", farmId], queryFn: () => api.getZones(farmId) });

  const mapping = query.data?.latest?.cluster_labels ?? {};
  const fields = query.data?.fields ?? [];

  const grouped = useMemo(() => {
    const bucket: Record<number, string[]> = {};
    fields.forEach((field: any) => {
      const cluster = mapping[field.id] ?? field.zone_cluster_id ?? 0;
      bucket[cluster] = bucket[cluster] ?? [];
      bucket[cluster].push(field.name);
    });
    return bucket;
  }, [fields, mapping]);

  const pcaPoints = fields.map((field: any, idx: number) => ({
    name: field.name,
    x: idx + 1,
    y: field.zone_cluster_id ?? 0,
    cluster: field.zone_cluster_id ?? 0,
  }));

  return (
    <div className="space-y-4">
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {Object.entries(grouped).map(([clusterId, fieldNames]) => (
          <ZoneCard key={clusterId} title={`Zone ${String.fromCharCode(65 + Number(clusterId))}`} clusterId={Number(clusterId)} fields={fieldNames} />
        ))}
      </section>

      <section className="rounded-xl border border-green-700/30 bg-farm-surface/90 p-4">
        <p className="mb-2 text-xs uppercase tracking-[0.2em] text-farm-muted">PCA Explained Variance</p>
        <div className="space-y-2">
          {(query.data?.latest?.pca_explained_variance ?? []).map((value, index) => (
            <div key={index}>
              <div className="mb-1 flex items-center justify-between text-xs text-gray-300">
                <span>PC{index + 1}</span>
                <span>{(value * 100).toFixed(1)}%</span>
              </div>
              <div className="h-2 rounded-full bg-green-950/70">
                <div className="h-full rounded-full bg-farm-accent" style={{ width: `${Math.max(2, value * 100)}%` }} />
              </div>
            </div>
          ))}
        </div>
      </section>

      <ScatterPca points={pcaPoints} />
    </div>
  );
}
