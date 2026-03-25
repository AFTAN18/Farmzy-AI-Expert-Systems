export type SensorReading = {
  id: string;
  field_id: string;
  farm_id: string;
  thingspeak_entry_id?: number;
  recorded_at: string;
  nitrogen?: number | null;
  phosphorus?: number | null;
  potassium?: number | null;
  temperature?: number | null;
  humidity?: number | null;
  ph?: number | null;
  gas_ppm?: number | null;
  soil_moisture?: number | null;
};

export type FarmItem = {
  id: string;
  name: string;
  location?: string | null;
  thingspeak_channel_id?: string | null;
  has_api_key?: boolean;
};

export type ThingSpeakConfig = {
  id: string;
  name?: string;
  thingspeak_channel_id?: string | null;
  thingspeak_read_api_key?: string | null;
  has_api_key?: boolean;
};

export type IrrigationPrediction = {
  id?: string;
  field_id?: string;
  sensor_reading_id?: string;
  predicted_at?: string;
  water_requirement_liters?: number;
  irrigation_decision?: "ON" | "OFF" | string;
  confidence_score?: number;
  expert_rule_fired?: string;
  fuzzy_membership_score?: number;
  reasoning_trace?: Record<string, unknown>;
  rules_fired?: string[];
};

export type CropRecommendation = {
  id?: string;
  field_id?: string;
  recommended_at?: string;
  top_crop_1?: string;
  top_crop_2?: string;
  top_crop_3?: string;
  probabilities?: Record<string, number>;
  naive_bayes_confidence?: number;
};

export type AlertItem = {
  id: string;
  farm_id: string;
  field_id?: string | null;
  alert_type: string;
  severity: "info" | "warning" | "critical" | string;
  message: string;
  is_resolved: boolean;
  triggered_at: string;
  resolved_at?: string | null;
};

export type RuleItem = {
  rule_id: string;
  rule_name: string;
  condition_description: string;
  action_description: string;
  priority: number;
  is_active: boolean;
};

export type ZoneSnapshot = {
  id?: string;
  farm_id?: string;
  run_at?: string;
  num_clusters?: number;
  cluster_centers?: number[][];
  cluster_labels?: Record<string, number>;
  pca_explained_variance?: number[];
  pca_components?: number[][];
  inertia?: number;
};
