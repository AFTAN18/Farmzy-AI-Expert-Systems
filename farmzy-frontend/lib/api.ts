import type {
  AlertItem,
  CropRecommendation,
  IrrigationPrediction,
  RuleItem,
  SensorReading,
  ZoneSnapshot,
} from "@/lib/types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(`API ${response.status}: ${text || response.statusText}`);
  }

  return (await response.json()) as T;
}

export const api = {
  getDashboard: (farmId: string) => request<{ farm_id: string; rows: any[] }>(`/api/farms/${farmId}/dashboard`),
  getReadings: (farmId: string, limit = 100, page = 1) =>
    request<{ items: SensorReading[] }>(`/api/farms/${farmId}/readings?limit=${limit}&page=${page}`),
  getPredictions: (farmId: string, limit = 100) =>
    request<{ items: IrrigationPrediction[] }>(`/api/farms/${farmId}/predictions?limit=${limit}`),
  getCrops: (farmId: string) => request<{ items: CropRecommendation[] }>(`/api/farms/${farmId}/crops`),
  getZones: (farmId: string) => request<{ latest: ZoneSnapshot | null; fields: any[] }>(`/api/farms/${farmId}/zones`),
  getAlerts: (farmId: string, includeResolved = false) =>
    request<{ items: AlertItem[] }>(`/api/farms/${farmId}/alerts?include_resolved=${includeResolved}`),
  resolveAlert: (farmId: string, alertId: string) =>
    request(`/api/farms/${farmId}/alerts/${alertId}/resolve`, { method: "POST" }),
  getModels: () => request<Record<string, unknown>>(`/api/models/status`),
  retrainModels: () => request(`/api/models/retrain`, { method: "POST" }),
  getRules: () => request<{ items: RuleItem[] }>(`/api/expert-system/rules`),
  createRule: (payload: RuleItem) =>
    request(`/api/expert-system/rules`, { method: "POST", body: JSON.stringify(payload) }),
  updateRule: (ruleId: string, payload: RuleItem) =>
    request(`/api/expert-system/rules/${ruleId}`, { method: "PUT", body: JSON.stringify(payload) }),
  explainReading: (readingId: string) => request(`/api/expert-system/explain/${readingId}`),
};

export class FarmWebSocket {
  private socket: WebSocket | null = null;

  connect(farmId: string, onMessage: (payload: any) => void) {
    this.disconnect();
    const base = process.env.NEXT_PUBLIC_WS_URL ?? "ws://localhost:8000";
    this.socket = new WebSocket(`${base}/ws/farm/${farmId}`);

    this.socket.onmessage = (event) => {
      try {
        onMessage(JSON.parse(event.data));
      } catch {
        // ignore malformed events
      }
    };
  }

  disconnect() {
    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }
  }
}
