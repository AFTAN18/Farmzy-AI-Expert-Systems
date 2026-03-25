"use client";

import { Line, LineChart, ResponsiveContainer, Tooltip } from "recharts";

import type { SensorReading } from "@/lib/types";

type SensorCardProps = {
  label: string;
  unit: string;
  value: number | null | undefined;
  data: SensorReading[];
  metric: keyof SensorReading;
  low?: number;
  high?: number;
};

function getStatus(value: number | null | undefined, low?: number, high?: number) {
  if (value === null || value === undefined) {
    return "UNKNOWN";
  }
  if (low !== undefined && value < low) {
    return "WARNING";
  }
  if (high !== undefined && value > high) {
    return "CRITICAL";
  }
  return "OPTIMAL";
}

export function SensorCard({ label, unit, value, data, metric, low, high }: SensorCardProps) {
  const status = getStatus(value, low, high);
  const border = status === "OPTIMAL" ? "border-green-600/40" : status === "WARNING" ? "border-amber-500/50" : "border-red-500/50";

  return (
    <div className={`rounded-xl border bg-farm-surface/90 p-4 ${border}`}>
      <div className="mb-3 flex items-center justify-between">
        <p className="text-sm text-gray-200">{label}</p>
        <span className="rounded-full bg-green-950/60 px-2 py-1 text-[10px] tracking-wide text-farm-accent">{status}</span>
      </div>
      <p className="text-2xl font-semibold text-farm-accent">
        {value ?? "-"} {unit}
      </p>
      <div className="mt-3 h-16">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data.slice().reverse()}>
            <Tooltip />
            <Line
              dataKey={metric as string}
              type="monotone"
              stroke="#4ADE80"
              strokeWidth={2}
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
