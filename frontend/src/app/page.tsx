"use client";

import React, { useEffect, useState } from "react";
import { Sparkles, Utensils, MapPin, Search, RefreshCw, Star, Sliders, CheckCircle2 } from "lucide-react";
import { fetchLocations, fetchCuisines, fetchRecommendations, RestaurantCard as CardType } from "@/lib/api";
import RestaurantCardItem from "@/components/RestaurantCard";

export default function Home() {
  const [locations, setLocations] = useState<string[]>([]);
  const [cuisines, setCuisines] = useState<string[]>([]);

  // Form states
  const [selectedLocation, setSelectedLocation] = useState<string>("");
  const [selectedCuisine, setSelectedCuisine] = useState<string>("");
  const [budgetLevel, setBudgetLevel] = useState<string>("medium");
  const [minRating, setMinRating] = useState<number>(3.5);
  const [selectedExtras, setSelectedExtras] = useState<string[]>([]);

  // UI status states
  const [loading, setLoading] = useState<boolean>(false);
  const [recommendations, setRecommendations] = useState<CardType[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [searched, setSearched] = useState<boolean>(false);

  const availableExtras = [
    "Family-friendly",
    "Quick service",
    "Romantic ambiance",
    "Outdoor seating",
    "Vegetarian-friendly",
    "Late-night dining",
    "Rooftop seating",
    "Pet-friendly"
  ];

  useEffect(() => {
    async function loadDropdowns() {
      const locs = await fetchLocations();
      setLocations(locs);
      if (locs.length > 0) setSelectedLocation(locs[0]);

      const cuis = await fetchCuisines();
      setCuisines(cuis);
    }
    loadDropdowns();
  }, []);

  const handleExtraToggle = (extra: string) => {
    setSelectedExtras((prev) =>
      prev.includes(extra) ? prev.filter((e) => e !== extra) : [...prev, extra]
    );
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedLocation) {
      setError("Please select a location");
      return;
    }

    setLoading(true);
    setError(null);
    setSearched(true);

    try {
      const res = await fetchRecommendations({
        location: selectedLocation,
        cuisine: selectedCuisine || undefined,
        budget_level: budgetLevel,
        min_rating: minRating,
        extras: selectedExtras,
      });

      setRecommendations(res.recommendations);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Failed to fetch recommendations. Please verify the backend API.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen pb-16">
      {/* Header Banner */}
      <header className="hero-gradient py-12 px-6 shadow-xs border-b border-purple-100">
        <div className="max-w-6xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 bg-white/80 backdrop-blur-md px-4 py-1.5 rounded-full text-xs font-semibold text-purple-900 shadow-xs mb-4">
            <span className="w-2 h-2 rounded-full bg-pink-500 animate-pulse" />
            Gastronomic Discovery Engine
          </div>
          <h1 className="text-4xl md:text-5xl font-extrabold text-gray-900 tracking-tight mb-3">
            AI Restaurant Recommender
          </h1>
          <p className="text-purple-900/80 max-w-2xl mx-auto text-base md:text-lg">
            Personalized, intelligent dining recommendations powered by Groq LLM and Zomato dataset insights.
          </p>
        </div>
      </header>

      <div className="max-w-6xl mx-auto px-4 mt-8 grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Sidebar Controls */}
        <aside className="lg:col-span-4">
          <form onSubmit={handleSearch} className="glass-card rounded-2xl p-6 sticky top-6">
            <div className="flex items-center justify-between mb-6 pb-3 border-b border-purple-100">
              <h2 className="text-lg font-bold text-gray-900 flex items-center gap-2">
                <Sliders className="w-5 h-5 text-pink-500" />
                Your Preferences
              </h2>
              <span className="text-xs bg-pink-100 text-pink-700 px-2 py-0.5 rounded-md font-medium">
                Live Filter
              </span>
            </div>

            {/* Location Dropdown */}
            <div className="mb-5">
              <label className="block text-sm font-semibold text-gray-800 mb-2 flex items-center gap-1.5">
                <MapPin className="w-4 h-4 text-pink-500" />
                Select Area / Location
              </label>
              <select
                value={selectedLocation}
                onChange={(e) => setSelectedLocation(e.target.value)}
                className="w-full bg-white border border-purple-200 rounded-xl px-3.5 py-2.5 text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-pink-400"
              >
                {locations.length === 0 && <option value="">Loading locations...</option>}
                {locations.map((loc) => (
                  <option key={loc} value={loc}>
                    {loc}
                  </option>
                ))}
              </select>
            </div>

            {/* Cuisine Selector */}
            <div className="mb-5">
              <label className="block text-sm font-semibold text-gray-800 mb-2 flex items-center gap-1.5">
                <Utensils className="w-4 h-4 text-purple-500" />
                Cuisine Preference (Optional)
              </label>
              <select
                value={selectedCuisine}
                onChange={(e) => setSelectedCuisine(e.target.value)}
                className="w-full bg-white border border-purple-200 rounded-xl px-3.5 py-2.5 text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-pink-400"
              >
                <option value="">Any Cuisine</option>
                {cuisines.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
            </div>

            {/* Budget Range */}
            <div className="mb-5">
              <label className="block text-sm font-semibold text-gray-800 mb-2">
                Budget Level (Cost for 2)
              </label>
              <div className="grid grid-cols-3 gap-2">
                {[
                  { id: "low", label: "Low", range: "₹0 - ₹300" },
                  { id: "medium", label: "Medium", range: "₹300 - ₹700" },
                  { id: "high", label: "High", range: "₹700+" },
                ].map((b) => (
                  <button
                    key={b.id}
                    type="button"
                    onClick={() => setBudgetLevel(b.id)}
                    className={`p-2 rounded-xl text-xs font-semibold border transition-all text-center ${
                      budgetLevel === b.id
                        ? "bg-pink-500 text-white border-pink-500 shadow-xs"
                        : "bg-white text-gray-700 border-purple-200 hover:border-pink-300"
                    }`}
                  >
                    <div>{b.label}</div>
                    <div className="text-[10px] opacity-80 mt-0.5">{b.range}</div>
                  </button>
                ))}
              </div>
            </div>

            {/* Min Rating */}
            <div className="mb-6">
              <div className="flex justify-between items-center mb-2">
                <label className="text-sm font-semibold text-gray-800 flex items-center gap-1.5">
                  <Star className="w-4 h-4 text-amber-500" />
                  Minimum Rating
                </label>
                <span className="text-sm font-bold text-amber-600 bg-amber-50 px-2 py-0.5 rounded-md border border-amber-200">
                  {minRating.toFixed(1)} ⭐
                </span>
              </div>
              <input
                type="range"
                min="0"
                max="5"
                step="0.1"
                value={minRating}
                onChange={(e) => setMinRating(parseFloat(e.target.value))}
                className="w-full accent-pink-500 cursor-pointer"
              />
            </div>

            {/* Extras Badges */}
            <div className="mb-6">
              <label className="block text-sm font-semibold text-gray-800 mb-2">
                Extras & Vibe Filters
              </label>
              <div className="flex flex-wrap gap-1.5">
                {availableExtras.map((extra) => {
                  const active = selectedExtras.includes(extra);
                  return (
                    <button
                      key={extra}
                      type="button"
                      onClick={() => handleExtraToggle(extra)}
                      className={`px-2.5 py-1 rounded-lg text-xs font-medium border transition-all ${
                        active
                          ? "bg-purple-600 text-white border-purple-600 shadow-2xs"
                          : "bg-white text-gray-600 border-purple-200 hover:border-purple-400"
                      }`}
                    >
                      {extra}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading}
              className="w-full btn-rose font-bold py-3 rounded-xl flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
            >
              {loading ? (
                <>
                  <RefreshCw className="w-5 h-5 animate-spin" />
                  AI Analyzing Restaurants...
                </>
              ) : (
                <>
                  <Search className="w-5 h-5" />
                  Find Top Recommendations
                </>
              )}
            </button>
          </form>
        </aside>

        {/* Results Area */}
        <section className="lg:col-span-8">
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 p-4 rounded-2xl mb-6 text-sm flex items-center gap-2">
              ⚠️ {error}
            </div>
          )}

          {loading && (
            <div className="glass-card rounded-2xl p-12 text-center">
              <div className="inline-flex p-4 rounded-full bg-pink-100 text-pink-600 mb-4 animate-bounce">
                <Sparkles className="w-8 h-8" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-2">
                Consulting Groq LLM Intelligence...
              </h3>
              <p className="text-purple-900/70 text-sm max-w-md mx-auto">
                Filtering Zomato dataset candidates and crafting custom culinary recommendations.
              </p>
            </div>
          )}

          {!loading && searched && recommendations.length === 0 && !error && (
            <div className="glass-card rounded-2xl p-12 text-center">
              <div className="text-4xl mb-3">🔍</div>
              <h3 className="text-xl font-bold text-gray-900 mb-2">No Matching Restaurants Found</h3>
              <p className="text-purple-900/70 text-sm max-w-md mx-auto">
                Try lowering the minimum rating or clearing cuisine filters to see more results.
              </p>
            </div>
          )}

          {!loading && recommendations.length > 0 && (
            <div className="space-y-5">
              <div className="flex items-center justify-between px-1">
                <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2">
                  <CheckCircle2 className="w-5 h-5 text-emerald-500" />
                  Top Recommended Spots ({recommendations.length})
                </h2>
                <span className="text-xs text-purple-900/60 font-medium">
                  Sorted by AI match ranking
                </span>
              </div>

              {recommendations.map((card) => (
                <RestaurantCardItem key={card.rank} card={card} />
              ))}
            </div>
          )}

          {!searched && !loading && (
            <div className="glass-card rounded-2xl p-12 text-center">
              <div className="inline-flex p-4 rounded-full bg-purple-100 text-purple-600 mb-4">
                <Utensils className="w-8 h-8" />
              </div>
              <h3 className="text-2xl font-extrabold text-gray-900 mb-2">
                Ready for Gastronomic Discovery?
              </h3>
              <p className="text-purple-900/70 text-sm max-w-md mx-auto mb-6">
                Select your preferred location, budget level, and cuisine in the left sidebar and click <strong>Find Top Recommendations</strong>.
              </p>
            </div>
          )}
        </section>
      </div>
    </main>
  );
}
