"use client";

import { useQuery } from "@tanstack/react-query";

import { CropRecommendationCard } from "@/components/crop-recommendation";
import { api } from "@/lib/api";
import { useFarmStore } from "@/store/farm-store";

export default function CropsPage() {
  const farmId = useFarmStore((state) => state.selectedFarmId);
  const query = useQuery({ queryKey: ["crops", farmId], queryFn: () => api.getCrops(farmId) });

  const latest = query.data?.items?.[0] ?? null;

  return (
    <div className="space-y-4">
      <CropRecommendationCard recommendation={latest} />

      <section className="rounded-xl border border-green-700/30 bg-farm-surface/90 p-4">
        <p className="mb-3 text-xs uppercase tracking-[0.2em] text-farm-muted">Historical Recommendations</p>
        <div className="overflow-x-auto">
          <table className="min-w-full text-left text-sm">
            <thead className="text-xs uppercase text-farm-muted">
              <tr>
                <th className="px-2 py-2">Time</th>
                <th className="px-2 py-2">Top 1</th>
                <th className="px-2 py-2">Top 2</th>
                <th className="px-2 py-2">Top 3</th>
                <th className="px-2 py-2">Confidence</th>
              </tr>
            </thead>
            <tbody>
              {(query.data?.items ?? []).map((item) => (
                <tr key={item.id} className="border-t border-green-900/40">
                  <td className="px-2 py-2">{item.recommended_at ? new Date(item.recommended_at).toLocaleString() : "-"}</td>
                  <td className="px-2 py-2">{item.top_crop_1 ?? "-"}</td>
                  <td className="px-2 py-2">{item.top_crop_2 ?? "-"}</td>
                  <td className="px-2 py-2">{item.top_crop_3 ?? "-"}</td>
                  <td className="px-2 py-2">{((item.naive_bayes_confidence ?? 0) * 100).toFixed(1)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
