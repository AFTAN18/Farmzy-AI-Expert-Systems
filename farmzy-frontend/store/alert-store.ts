import { create } from "zustand";

import type { AlertItem } from "@/lib/types";

type AlertStore = {
  activeAlerts: AlertItem[];
  unreadCount: number;
  setAlerts: (alerts: AlertItem[]) => void;
  pushAlert: (alert: AlertItem) => void;
  markRead: () => void;
};

export const useAlertStore = create<AlertStore>((set) => ({
  activeAlerts: [],
  unreadCount: 0,
  setAlerts: (alerts) => set({ activeAlerts: alerts }),
  pushAlert: (alert) =>
    set((state) => ({
      activeAlerts: [alert, ...state.activeAlerts.filter((item) => item.id !== alert.id)],
      unreadCount: state.unreadCount + 1,
    })),
  markRead: () => set({ unreadCount: 0 }),
}));
