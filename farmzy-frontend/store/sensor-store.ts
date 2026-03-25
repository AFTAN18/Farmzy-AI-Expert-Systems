import { create } from "zustand";

import type { SensorReading } from "@/lib/types";

type SensorStore = {
  latestReadings: SensorReading[];
  sparklineData: Record<string, SensorReading[]>;
  pushReading: (reading: SensorReading) => void;
  setLatestReadings: (readings: SensorReading[]) => void;
};

export const useSensorStore = create<SensorStore>((set) => ({
  latestReadings: [],
  sparklineData: {},
  pushReading: (reading) =>
    set((state) => {
      const nextLatest = [reading, ...state.latestReadings.filter((item) => item.id !== reading.id)].slice(0, 50);
      const bucket = state.sparklineData[reading.field_id] ?? [];
      const nextBucket = [reading, ...bucket.filter((item) => item.id !== reading.id)].slice(0, 20);

      return {
        latestReadings: nextLatest,
        sparklineData: {
          ...state.sparklineData,
          [reading.field_id]: nextBucket,
        },
      };
    }),
  setLatestReadings: (readings) =>
    set(() => {
      const grouped: Record<string, SensorReading[]> = {};
      readings.forEach((item) => {
        grouped[item.field_id] = grouped[item.field_id] ?? [];
        grouped[item.field_id].push(item);
      });
      Object.keys(grouped).forEach((key) => {
        grouped[key] = grouped[key].slice(0, 20);
      });
      return { latestReadings: readings, sparklineData: grouped };
    }),
}));
