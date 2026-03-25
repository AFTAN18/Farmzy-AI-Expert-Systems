"use client";

import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { ChartSensor } from "@/components/chart-sensor";
import { ConnectionStatus } from "@/components/connection-status";
import { api } from "@/lib/api";
import { useFarmStore } from "@/store/farm-store";

const sensors = ["nitrogen", "phosphorus", "potassium", "temperature", "humidity", "ph", "gas_ppm", "soil_moisture"] as const;

export default function SensorsPage() {
  const farmId = useFarmStore((state) => state.selectedFarmId);
  const [page, setPage] = useState(1);
  const query = useQuery({ queryKey: ["readings", farmId, page], queryFn: () => api.getReadings(farmId, 100, page) });

  const chartData = useMemo(
    () =>
      (query.data?.items ?? [])
        .slice(0, 100)
        .map((reading) => ({
          time: new Date(reading.recorded_at).toLocaleTimeString(),
          ...reading,
        }))
        .reverse(),
    [query.data],
  );

  return (
    <div className="space-y-4">
      <ConnectionStatus channel={process.env.NEXT_PUBLIC_THINGSPEAK_CHANNEL ?? "2972911"} connected={true} lastSyncSeconds={23} />

      <section className="grid gap-4 lg:grid-cols-2">
        {sensors.map((sensorKey) => (
          <ChartSensor key={sensorKey} title={sensorKey.replace("_", " ")} data={chartData} dataKey={sensorKey} />
        ))}
      </section>

      <section className="rounded-xl border border-green-700/30 bg-farm-surface/90 p-3">
        <div className="mb-2 flex items-center justify-between">
          <p className="text-xs uppercase tracking-[0.2em] text-farm-muted">Raw Sensor Readings</p>
          <button className="rounded-md border border-green-700/40 px-2 py-1 text-xs">Export CSV</button>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full text-left text-sm">
            <thead className="text-xs uppercase text-farm-muted">
              <tr>
                <th className="px-2 py-2">Timestamp</th>
                <th className="px-2 py-2">N</th>
                <th className="px-2 py-2">P</th>
                <th className="px-2 py-2">K</th>
                <th className="px-2 py-2">Temp</th>
                <th className="px-2 py-2">Humidity</th>
                <th className="px-2 py-2">pH</th>
                <th className="px-2 py-2">Gas</th>
                <th className="px-2 py-2">Moisture</th>
              </tr>
            </thead>
            <tbody>
              {(query.data?.items ?? []).map((row) => {
                const critical = (row.soil_moisture ?? 100) < 20 || (row.temperature ?? 0) > 38;
                return (
                  <tr key={row.id} className={critical ? "bg-red-900/20" : "border-t border-green-900/40"}>
                    <td className="px-2 py-2">{new Date(row.recorded_at).toLocaleString()}</td>
                    <td className="px-2 py-2">{row.nitrogen ?? "-"}</td>
                    <td className="px-2 py-2">{row.phosphorus ?? "-"}</td>
                    <td className="px-2 py-2">{row.potassium ?? "-"}</td>
                    <td className="px-2 py-2">{row.temperature ?? "-"}</td>
                    <td className="px-2 py-2">{row.humidity ?? "-"}</td>
                    <td className="px-2 py-2">{row.ph ?? "-"}</td>
                    <td className="px-2 py-2">{row.gas_ppm ?? "-"}</td>
                    <td className="px-2 py-2">{row.soil_moisture ?? "-"}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        <div className="mt-3 flex justify-end gap-2">
          <button className="rounded-md border border-green-700/40 px-2 py-1 text-xs" onClick={() => setPage((p) => Math.max(1, p - 1))}>
            Prev
          </button>
          <button className="rounded-md border border-green-700/40 px-2 py-1 text-xs" onClick={() => setPage((p) => p + 1)}>
            Next
          </button>
        </div>
      </section>
    </div>
  );
}
