import React from "react";
import { Star, MapPin, Utensils, CreditCard, Sparkles } from "lucide-react";
import { RestaurantCard as CardType } from "@/lib/api";

interface Props {
  card: CardType;
}

export default function RestaurantCardItem({ card }: Props) {
  return (
    <div className="glass-card rounded-2xl p-6 transition-all duration-300 relative overflow-hidden group">
      {/* Top accent bar */}
      <div className="absolute top-0 left-0 right-0 h-1.5 bg-gradient-to-r from-pink-400 via-purple-300 to-pink-300" />

      <div className="flex flex-col md:flex-row md:items-start justify-between gap-4 mb-4">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <span className="w-8 h-8 rounded-full bg-gradient-to-r from-pink-500 to-rose-400 text-white font-bold flex items-center justify-center text-sm shadow-md">
              #{card.rank}
            </span>
            <h3 className="text-xl font-bold text-gray-900 group-hover:text-pink-600 transition-colors">
              {card.name}
            </h3>
          </div>

          <div className="flex flex-wrap items-center gap-y-1 gap-x-3 text-sm text-purple-900/70 mt-2">
            <span className="flex items-center gap-1">
              <MapPin className="w-4 h-4 text-pink-500" />
              {card.location}
            </span>
            <span>•</span>
            <span className="flex items-center gap-1">
              <Utensils className="w-4 h-4 text-purple-500" />
              {card.cuisines}
            </span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1 bg-amber-50 px-3 py-1.5 rounded-xl border border-amber-200 shadow-xs">
            <Star className="w-4 h-4 fill-amber-400 text-amber-400" />
            <span className="font-bold text-amber-900 text-sm">{card.rating}</span>
          </div>
          <div className="flex items-center gap-1 bg-purple-50 px-3 py-1.5 rounded-xl border border-purple-200 text-purple-900 text-sm font-semibold">
            <CreditCard className="w-4 h-4 text-purple-500" />
            {card.cost_for_two}
          </div>
        </div>
      </div>

      {/* AI Reasoning box */}
      <div className="mt-4 p-4 rounded-xl bg-gradient-to-r from-purple-50/80 to-pink-50/50 border border-purple-100/80 text-sm text-gray-800 leading-relaxed">
        <div className="flex items-center gap-1.5 font-bold text-xs uppercase tracking-wider text-pink-600 mb-1.5">
          <Sparkles className="w-3.5 h-3.5" />
          AI Culinary Recommendation Reason
        </div>
        {card.explanation}
      </div>
    </div>
  );
}
