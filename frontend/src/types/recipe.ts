export type SearchPhase =
  | "generating_queries"
  | "searching_platforms"
  | "parsing_recipes"
  | "scoring"
  | "finalizing";

export interface ProgressEvent {
  step: number;
  total_steps: number;
  phase: SearchPhase;
  message: string;
}

export interface Recipe {
  id: string;
  source: "youtube" | "instagram";
  source_id: string;
  url: string;
  thumbnail_url: string;
  title: string;
  creator_name: string;
  creator_id: string;
  extracted_ingredients: string[];
  raw_description: string;
  duration?: number; // seconds (YouTube only)
  posted_at: string; // ISO datetime
  cache_expires_at: string; // ISO datetime
}

export interface ScoredRecipe {
  recipe: Recipe;
  coverage_score: number; // 0-1
  missing_ingredients: string[];
  reasoning: string;
}
