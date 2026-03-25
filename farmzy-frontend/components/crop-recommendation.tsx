"use client";

import type { CropRecommendation } from "@/lib/types";

type CropRecommendationProps = {
  recommendation: CropRecommendation | null;
};

export function CropRecommendationCard({ recommendation }: CropRecommendationProps) {
  const top = [recommendation?.top_crop_1, recommendation?.top_crop_2, recommendation?.top_crop_3].filter(Boolean);
  const probabilities = recommendation?.probabilities ?? {};

  return (
    <div className="rounded-xl border border-green-700/30 bg-farm-surface/90 p-4">
      <p className="text-xs uppercase tracking-[0.2em] text-farm-muted">Top Crop Recommendations</p>
      <div className="mt-3 space-y-3">
        {top.length === 0 ? <p className="text-sm text-gray-400">No recommendation yet.</p> : null}
        {top.map((crop) => {
          const score = Math.round((probabilities[crop!] ?? 0) * 100);
          return (
            <div key={crop}>
              <div className="mb-1 flex items-center justify-between text-sm">
                <span>{crop}</span>
                <span className="text-farm-accent">{score}%</span>
              </div>
              <div className="h-2 rounded-full bg-green-950/70">
                <div className="h-full rounded-full bg-farm-accent" style={{ width: `${score}%` }} />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
