"use client";

import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";

import { ScatterPca } from "@/components/scatter-pca";
import { ZoneCard } from "@/components/zone-card";
import { api } from "@/lib/api";
import { useFarmStore } from "@/store/farm-store";

function dot(a: number[], b: number[]) {
  const len = Math.min(a.length, b.length);
  let total = 0;
  for (let i = 0; i < len; i += 1) {
    total += a[i] * b[i];
  }
  return total;
}

export default function ZonesPage() {
  const farmId = useFarmStore((state) => state.selectedFarmId);
  const zonesQuery = useQuery({ queryKey: ["zones", farmId], queryFn: () => api.getZones(farmId) });
  const dashboardQuery = useQuery({ queryKey: ["dashboard", farmId], queryFn: () => api.getDashboard(farmId) });

  const mapping = zonesQuery.data?.latest?.cluster_labels ?? {};
  const fields = zonesQuery.data?.fields ?? [];
  const pcaVarianceRaw = zonesQuery.data?.latest?.pca_explained_variance ?? [];
  const pcaComponentsRaw = zonesQuery.data?.latest?.pca_components ?? [];

  const pcaVariance = (pcaVarianceRaw as Array<number | string>).map((v) => Number(v)).filter((v) => Number.isFinite(v));

  const zoneTitleByCluster = useMemo(() => {
    const clusters = Array.from(
      new Set(
        fields.map((field: any) => Number(mapping[field.id] ?? field.zone_cluster_id ?? 0)).filter((v) => Number.isFinite(v)),
      ),
    ).sort((a, b) => a - b);

    const result = new Map<number, string>();
    clusters.forEach((clusterId, index) => {
      result.set(clusterId, `Zone ${String.fromCharCode(65 + index)}`);
    });
    return result;
  }, [fields, mapping]);

  const groupedZones = useMemo(() => {
    const bucket = new Map<number, string[]>();
    fields.forEach((field: any) => {
      const clusterId = Number(mapping[field.id] ?? field.zone_cluster_id ?? 0);
      if (!bucket.has(clusterId)) {
        bucket.set(clusterId, []);
      }
      bucket.get(clusterId)!.push(field.name);
    });

    return Array.from(bucket.entries())
      .sort((a, b) => a[0] - b[0])
      .map(([clusterId, fieldNames], index) => ({
        clusterId,
        title: zoneTitleByCluster.get(clusterId) ?? `Zone ${String.fromCharCode(65 + index)}`,
        fieldNames,
      }));
  }, [fields, mapping, zoneTitleByCluster]);

  const pcaPoints = useMemo(() => {
    const dashboardRows = dashboardQuery.data?.rows ?? [];
    const components = Array.isArray(pcaComponentsRaw) ? (pcaComponentsRaw as Array<Array<number | string>>) : [];

    if (components.length >= 2 && dashboardRows.length > 0) {
      const pc1 = (components[0] ?? []).map((v) => Number(v));
      const pc2 = (components[1] ?? []).map((v) => Number(v));

      if (pc1.length > 0 && pc2.length > 0) {
        return dashboardRows.map((row: any) => {
          const vector = [
            Number(row.nitrogen ?? 0),
            Number(row.phosphorus ?? 0),
            Number(row.potassium ?? 0),
            Number(row.temperature ?? 0),
            Number(row.humidity ?? 0),
            Number(row.ph ?? 0),
            Number(row.gas_ppm ?? 0),
            Number(row.soil_moisture ?? 0),
          ];

          const cluster = Number(mapping[row.field_id] ?? row.zone_cluster_id ?? 0);
          return {
            name: row.field_name ?? row.field_id,
            x: Number(dot(vector, pc1).toFixed(3)),
            y: Number(dot(vector, pc2).toFixed(3)),
            cluster,
          };
        });
      }
    }

    return fields.map((field: any, index: number) => ({
      name: field.name,
      x: index + 1,
      y: Number(mapping[field.id] ?? field.zone_cluster_id ?? 0),
      cluster: Number(mapping[field.id] ?? field.zone_cluster_id ?? 0),
    }));
  }, [dashboardQuery.data, fields, mapping, pcaComponentsRaw]);

  return (
    <div className="space-y-4">
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {groupedZones.map((zone) => (
          <ZoneCard key={zone.clusterId} title={zone.title} clusterId={zone.clusterId} fields={zone.fieldNames} />
        ))}
      </section>

      <section className="rounded-xl border border-green-700/30 bg-farm-surface/90 p-4">
        <p className="mb-2 text-xs uppercase tracking-[0.2em] text-farm-muted">PCA Explained Variance</p>
        {pcaVariance.length === 0 ? (
          <p className="text-sm text-gray-400">PCA variance will appear after at least one successful clustering run.</p>
        ) : (
          <div className="space-y-2">
            {pcaVariance.map((value, index) => (
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
        )}
      </section>

      <ScatterPca
        points={pcaPoints}
        title={pcaVariance.length > 0 ? "PCA Scatter (PC1 vs PC2)" : "Field Scatter (Index vs Cluster)"}
        xLabel={pcaVariance.length > 0 ? "PC1" : "Field Index"}
        yLabel={pcaVariance.length > 0 ? "PC2" : "Cluster"}
      />
    </div>
  );
}
