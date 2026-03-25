import { create } from "zustand";

import type { FarmItem } from "@/lib/types";

type FarmStore = {
  selectedFarmId: string;
  farms: FarmItem[];
  setSelectedFarmId: (id: string) => void;
  setFarms: (farms: FarmItem[]) => void;
};

export const useFarmStore = create<FarmStore>((set) => ({
  selectedFarmId: "11111111-1111-1111-1111-111111111111",
  farms: [{ id: "11111111-1111-1111-1111-111111111111", name: "FARMZY Demo Farm" }],
  setSelectedFarmId: (id) => set({ selectedFarmId: id }),
  setFarms: (farms) => set({ farms }),
}));
