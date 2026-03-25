import { create } from "zustand";

type ModelStore = {
  modelStatus: Record<string, unknown>;
  lastRetrained: string | null;
  setModelStatus: (value: Record<string, unknown>) => void;
  markRetrained: () => void;
};

export const useModelStore = create<ModelStore>((set) => ({
  modelStatus: {},
  lastRetrained: null,
  setModelStatus: (value) => set({ modelStatus: value }),
  markRetrained: () => set({ lastRetrained: new Date().toISOString() }),
}));
