"use client";

import { useEffect, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { formatDistanceToNowStrict } from "date-fns";

import { AiDecisionPanel } from "@/components/ai-decision-panel";
import { ChartSensor } from "@/components/chart-sensor";
import { CropRecommendationCard } from "@/components/crop-recommendation";
import { MetricCard } from "@/components/metric-card";
import { SensorCard } from "@/components/sensor-card";
import { api } from "@/lib/api";
import type { SensorReading } from "@/lib/types";
import { useFarmStore } from "@/store/farm-store";
import { useSensorStore } from "@/store/sensor-store";

type SensorMetricKey =
  | "nitrogen"
  | "phosphorus"
  | "potassium"
  | "temperature"
  | "humidity"
  | "ph"
  | "gas_ppm"
  | "soil_moisture";

const sensorDefinitions: Array<{
  label: string;
  key: SensorMetricKey;
  unit: string;
  low?: number;
  high?: number;
}> = [
  { label: "Nitrogen", key: "nitrogen", unit: "mg/kg", low: 40, high: 140 },
  { label: "Phosphorus", key: "phosphorus", unit: "mg/kg", low: 20, high: 100 },
  { label: "Potassium", key: "potassium", unit: "mg/kg", low: 30, high: 200 },
  { label: "Temperature", key: "temperature", unit: "°C", low: 18, high: 35 },
  { label: "Humidity", key: "humidity", unit: "%", low: 40, high: 90 },
  { label: "pH", key: "ph", unit: "", low: 5.5, high: 7.5 },
  { label: "Air Quality", key: "gas_ppm", unit: "ppm", high: 400 },
  { label: "Soil Moisture", key: "soil_moisture", unit: "%", low: 25, high: 80 },
];

export default function DashboardPage() {
  const farmId = useFarmStore((state) => state.selectedFarmId);
  const sparklineData = useSensorStore((state) => state.sparklineData);
  const setLatestReadings = useSensorStore((state) => state.setLatestReadings);

  const readingsQuery = useQuery({ queryKey: ["readings", farmId], queryFn: () => api.getReadings(farmId, 50, 1) });
  const predictionsQuery = useQuery({ queryKey: ["predictions", farmId], queryFn: () => api.getPredictions(farmId, 20) });
  const cropsQuery = useQuery({ queryKey: ["crops", farmId], queryFn: () => api.getCrops(farmId) });
  const alertsQuery = useQuery({ queryKey: ["alerts", farmId], queryFn: () => api.getAlerts(farmId) });

  useEffect(() => {
    const data = readingsQuery.data?.items ?? [];
    setLatestReadings(data);
  }, [readingsQuery.data, setLatestReadings]);

  const latestReading = readingsQuery.data?.items?.[0];
  const latestPrediction = predictionsQuery.data?.items?.[0] ?? null;
  const latestCrop = cropsQuery.data?.items?.[0] ?? null;
  const activeAlerts = alertsQuery.data?.items ?? [];

  const sensorTrendData = useMemo(() => {
    const list = readingsQuery.data?.items ?? [];
    return list
      .slice(0, 24)
      .map((item) => ({
        time: new Date(item.recorded_at).toLocaleTimeString(),
        soil_moisture: item.soil_moisture ?? 0,
        temperature: item.temperature ?? 0,
      }))
      .reverse();
  }, [readingsQuery.data]);

  const statusSubtitle = latestPrediction?.predicted_at
    ? `${formatDistanceToNowStrict(new Date(latestPrediction.predicted_at), { addSuffix: true })}`
    : "No predictions yet";

  return (
    <div className="space-y-5">
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard label="Active Fields" value={new Set((readingsQuery.data?.items ?? []).map((r) => r.field_id)).size} />
        <MetricCard
          label="Current Irrigation"
          value={latestPrediction?.irrigation_decision ?? "OFF"}
          subtitle={`${(latestPrediction?.confidence_score ?? 0).toFixed(2)} confidence`}
        />
        <MetricCard label="Last Prediction" value={statusSubtitle} />
        <MetricCard label="Active Alerts" value={activeAlerts.length} />
      </section>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {sensorDefinitions.map((sensor) => (
          <SensorCard
            key={sensor.key}
            label={sensor.label}
            unit={sensor.unit}
            value={(latestReading?.[sensor.key] as SensorReading[SensorMetricKey] | null | undefined) ?? null}
            data={sparklineData[latestReading?.field_id ?? ""] ?? []}
            metric={sensor.key}
            low={sensor.low}
            high={sensor.high}
          />
        ))}
      </section>

      <AiDecisionPanel prediction={latestPrediction} />

      <section className="grid gap-4 lg:grid-cols-2">
        <ChartSensor title="24h Soil Moisture" data={sensorTrendData} dataKey="soil_moisture" color="#4ADE80" />
        <div className="space-y-4">
          <ChartSensor title="24h Temperature" data={sensorTrendData} dataKey="temperature" color="#F59E0B" />
          <CropRecommendationCard recommendation={latestCrop} />
        </div>
      </section>
    </div>
  );
}
