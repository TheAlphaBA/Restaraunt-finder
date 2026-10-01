export interface RecommendationRequest {
  location: string;
  cuisine?: string;
  budget_level: string;
  min_rating: number;
  extras?: string[];
}

export interface RestaurantCard {
  rank: number;
  name: string;
  cuisines: string;
  location: string;
  rating: number;
  cost_for_two: string;
  explanation: string;
}

export interface RecommendationResponse {
  recommendations: RestaurantCard[];
  candidates_found: number;
  filters_applied: {
    location: string;
    budget_level: string;
    cuisine: string;
    min_rating: number;
  };
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function fetchLocations(): Promise<string[]> {
  try {
    const res = await fetch(`${API_BASE}/api/locations`);
    if (!res.ok) return [];
    const data = await res.json();
    return data.locations || [];
  } catch {
    return [];
  }
}

export async function fetchCuisines(): Promise<string[]> {
  try {
    const res = await fetch(`${API_BASE}/api/cuisines`);
    if (!res.ok) return [];
    const data = await res.json();
    return data.cuisines || [];
  } catch {
    return [];
  }
}

export async function fetchRecommendations(
  req: RecommendationRequest
): Promise<RecommendationResponse> {
  const res = await fetch(`${API_BASE}/api/recommend`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(req),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: "API Error" }));
    throw new Error(errorData.detail || `Server returned ${res.status}`);
  }

  return res.json();
}
