export type DayOfWeek =
  | "monday"
  | "tuesday"
  | "wednesday"
  | "thursday"
  | "friday"
  | "saturday"
  | "sunday";

export const ALL_DAYS: DayOfWeek[] = [
  "monday",
  "tuesday",
  "wednesday",
  "thursday",
  "friday",
  "saturday",
  "sunday",
];

export interface MealSlot {
  id: string;
  day: DayOfWeek;
  enabled: boolean;
  recipe_id?: string;
  assigned_at?: string; // ISO datetime
  swap_count: number;
}

export interface MealPlan {
  id: string;
  user_id: string;
  ingredient_session_id: string;
  status: "draft" | "active";
  created_at: string; // ISO datetime
  slots: MealSlot[];
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  tool_calls?: Record<string, unknown>[];
  timestamp: string; // ISO datetime
}

export interface ChatResponse {
  response: string;
  plan: MealPlan;
  tool_calls: Record<string, unknown>[];
}

export interface GeneratePlanRequest {
  ingredient_session_id: string;
  enabled_days: DayOfWeek[];
  recipe_ids: string[];
}
