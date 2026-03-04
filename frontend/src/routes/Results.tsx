import { useLocation, useNavigate } from "react-router-dom";
import { useMemo, useState } from "react";
import Layout from "../components/Layout";
import PhoneCard from "../components/PhoneCard";
import ErrorBanner from "../components/ErrorBanner";
import type { PhoneRecommendation } from "../types";

interface LocationState {
  recommendations?: PhoneRecommendation[];
}

type SortMode = "match_desc" | "price_asc" | "price_desc";

export default function Results() {
  const navigate = useNavigate();
  const location = useLocation();
  const state = (location.state || {}) as LocationState;
  const [sortMode, setSortMode] = useState<SortMode>("match_desc");
  const [compareIds, setCompareIds] = useState<string[]>([]);

  const recommendations = state.recommendations ?? [];

  const sortedRecommendations = useMemo(() => {
    const recs = [...recommendations];
    switch (sortMode) {
      case "price_asc":
        return recs.sort(
          (a, b) => (a.phone.price || 0) - (b.phone.price || 0)
        );
      case "price_desc":
        return recs.sort(
          (a, b) => (b.phone.price || 0) - (a.phone.price || 0)
        );
      case "match_desc":
      default:
        return recs.sort(
          (a, b) => b.match_percentage - a.match_percentage
        );
    }
  }, [recommendations, sortMode]);

  const handleToggleCompare = (phoneId: string) => {
    setCompareIds(prev =>
      prev.includes(phoneId)
        ? prev.filter(id => id !== phoneId)
        : [...prev, phoneId]
    );
  };

  const handleGoToCompare = () => {
    const phones = recommendations
      .map(r => r.phone)
      .filter(p => p.id && compareIds.includes(p.id));
    navigate("/compare", {
      state: { phones }
    });
  };

  return (
    <Layout>
      <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h2 className="text-xl font-semibold text-slate-50">
            Your recommended phones
          </h2>
          <p className="mt-1 text-xs text-slate-400">
            Sorted by overall match score. You can re-sort by price, or select
            phones for side-by-side comparison.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-3 text-xs">
          <div className="flex items-center gap-1 rounded-full border border-slate-800 bg-slate-950/60 px-2 py-1">
            <span className="text-slate-400">Sort by</span>
            <select
              value={sortMode}
              onChange={e => setSortMode(e.target.value as SortMode)}
              className="rounded-full border border-slate-700 bg-slate-900/80 px-2 py-0.5 text-xs text-slate-100"
            >
              <option value="match_desc">Match (high to low)</option>
              <option value="price_asc">Price (low to high)</option>
              <option value="price_desc">Price (high to low)</option>
            </select>
          </div>
          <button
            type="button"
            disabled={compareIds.length < 2}
            onClick={handleGoToCompare}
            className="inline-flex items-center rounded-full border border-slate-700 bg-slate-950/80 px-3 py-1.5 text-xs font-medium text-slate-100 hover:border-brand/70 hover:text-brand disabled:opacity-50"
          >
            Compare {compareIds.length || ""} selected
          </button>
        </div>
      </div>

      {!recommendations.length && (
        <ErrorBanner message="No recommendations yet. Start by telling us your preferences." />
      )}

      <div className="grid gap-4 md:grid-cols-2">
        {sortedRecommendations.map(rec => (
          <PhoneCard
            key={rec.phone.id ?? rec.phone.name}
            rec={rec}
            onToggleCompare={rec.phone.id ? handleToggleCompare : undefined}
            selectedForCompare={
              rec.phone.id ? compareIds.includes(rec.phone.id) : false
            }
          />
        ))}
      </div>
    </Layout>
  );
}

