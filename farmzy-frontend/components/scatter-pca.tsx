"use client";

import { ResponsiveContainer, Scatter, ScatterChart, Tooltip, XAxis, YAxis } from "recharts";

type ScatterPcaProps = {
  points: Array<{ x: number; y: number; name: string; cluster: number }>;
};

export function ScatterPca({ points }: ScatterPcaProps) {
  return (
    <div className="h-72 rounded-xl border border-green-700/30 bg-farm-surface/90 p-3">
      <p className="mb-2 text-xs uppercase tracking-[0.2em] text-farm-muted">PCA Scatter (PC1 vs PC2)</p>
      <ResponsiveContainer width="100%" height="100%">
        <ScatterChart>
          <XAxis dataKey="x" name="PC1" stroke="#6B7280" />
          <YAxis dataKey="y" name="PC2" stroke="#6B7280" />
          <Tooltip cursor={{ strokeDasharray: "3 3" }} />
          <Scatter data={points} fill="#4ADE80" />
        </ScatterChart>
      </ResponsiveContainer>
    </div>
  );
}
