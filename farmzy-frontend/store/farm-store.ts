import { create } from "zustand";

type FarmStore = {
  selectedFarmId: string;
  farms: { id: string; name: string }[];
  setSelectedFarmId: (id: string) => void;
  setFarms: (farms: { id: string; name: string }[]) => void;
};

export const useFarmStore = create<FarmStore>((set) => ({
  selectedFarmId: "11111111-1111-1111-1111-111111111111",
  farms: [{ id: "11111111-1111-1111-1111-111111111111", name: "FARMZY Demo Farm" }],
  setSelectedFarmId: (id) => set({ selectedFarmId: id }),
  setFarms: (farms) => set({ farms }),
}));
