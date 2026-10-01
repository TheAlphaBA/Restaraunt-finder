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

function getApiBaseUrl(): string {
  let url = process.env.NEXT_PUBLIC_API_URL;
  if (!url || !url.trim()) {
    return "https://restaraunt-finder-production.up.railway.app";
  }
  url = url.trim();
  if (!url.startsWith("http://") && !url.startsWith("https://")) {
    url = `https://${url}`;
  }
  return url.replace(/\/+$/, "");
}

const API_BASE = getApiBaseUrl();

export async function fetchLocations(): Promise<string[]> {
  try {
    const res = await fetch(`${API_BASE}/api/locations`);
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    const data = await res.json();
    return data.locations || [];
  } catch (err) {
    console.error("Failed to fetch locations from backend:", err, "API_BASE:", API_BASE);
    throw err;
  }
}

export async function fetchCuisines(): Promise<string[]> {
  try {
    const res = await fetch(`${API_BASE}/api/cuisines`);
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    const data = await res.json();
    return data.cuisines || [];
  } catch (err) {
    console.error("Failed to fetch cuisines from backend:", err, "API_BASE:", API_BASE);
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
