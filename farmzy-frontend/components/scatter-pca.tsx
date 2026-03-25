"use client";

import { ResponsiveContainer, Scatter, ScatterChart, Tooltip, XAxis, YAxis } from "recharts";

type ScatterPcaProps = {
  points: Array<{ x: number; y: number; name: string; cluster: number }>;
  title?: string;
  xLabel?: string;
  yLabel?: string;
  emptyMessage?: string;
};

export function ScatterPca({
  points,
  title = "PCA Scatter (PC1 vs PC2)",
  xLabel = "PC1",
  yLabel = "PC2",
  emptyMessage = "No scatter data available yet.",
}: ScatterPcaProps) {
  return (
    <div className="h-72 rounded-xl border border-green-700/30 bg-farm-surface/90 p-3">
      <p className="mb-2 text-xs uppercase tracking-[0.2em] text-farm-muted">{title}</p>
      {points.length === 0 ? (
        <div className="flex h-[88%] items-center justify-center text-sm text-gray-400">{emptyMessage}</div>
      ) : (
        <ResponsiveContainer width="100%" height="100%">
          <ScatterChart>
            <XAxis dataKey="x" name={xLabel} stroke="#6B7280" />
            <YAxis dataKey="y" name={yLabel} stroke="#6B7280" />
            <Tooltip cursor={{ strokeDasharray: "3 3" }} />
            <Scatter data={points} fill="#4ADE80" />
          </ScatterChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
