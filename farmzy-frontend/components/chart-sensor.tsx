"use client";

import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

type ChartSensorProps = {
  title: string;
  data: Array<Record<string, number | string | null>>;
  dataKey: string;
  color?: string;
};

export function ChartSensor({ title, data, dataKey, color = "#4ADE80" }: ChartSensorProps) {
  return (
    <div className="h-56 rounded-xl border border-green-700/30 bg-farm-surface/90 p-3">
      <p className="mb-2 text-xs uppercase tracking-[0.2em] text-farm-muted">{title}</p>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data}>
          <XAxis dataKey="time" stroke="#6B7280" hide />
          <YAxis stroke="#6B7280" width={35} />
          <Tooltip />
          <Line type="monotone" dataKey={dataKey} stroke={color} strokeWidth={2} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
