import { useState } from "react";
import type { RecommendationRequest, RecommendationResponse } from "../types";
import { fetchRecommendations } from "../lib/api";
import LoadingSpinner from "./LoadingSpinner";
import ErrorBanner from "./ErrorBanner";

interface Props {
  onRecommendations: (data: RecommendationResponse, request: RecommendationRequest) => void;
}

export default function PreferenceForm({ onRecommendations }: Props) {
  const [maxBudget, setMaxBudget] = useState<number | undefined>(30000);
  const [cameraPriority, setCameraPriority] = useState(70);
  const [batteryPriority, setBatteryPriority] = useState(70);
  const [performancePriority, setPerformancePriority] = useState(60);
  const [storagePriority, setStoragePriority] = useState(50);
  const [ramPriority, setRamPriority] = useState(50);
  const [osPreference, setOsPreference] = useState<string | undefined>();
  const [primaryUse, setPrimaryUse] = useState<string>("normal");
  const [minRam, setMinRam] = useState<number | undefined>(4);
  const [minStorage, setMinStorage] = useState<number | undefined>(64);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    const sliders = {
      budget: 100 - Math.round(((cameraPriority + batteryPriority + performancePriority) / 3)),
      camera: cameraPriority,
      battery: batteryPriority,
      performance: performancePriority,
      storage: storagePriority,
      ram: ramPriority
    };

    const sum = Object.values(sliders).reduce((acc, v) => acc + v, 0) || 1;
    const weights = Object.fromEntries(
      Object.entries(sliders).map(([k, v]) => [k, v / sum])
    ) as RecommendationRequest["weights"];

    const payload: RecommendationRequest = {
      max_budget: maxBudget,
      min_ram: minRam,
      min_storage: minStorage,
      os_preference: osPreference,
      primary_use: primaryUse,
      weights
    };

    try {
      const data = await fetchRecommendations(payload);
      if (!data.recommendations.length) {
        setError("No matching phones found. Try relaxing your filters.");
      } else {
        onRecommendations(data, payload);
      }
    } catch (err) {
      setError("Failed to fetch recommendations. Please ensure the backend is running.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="space-y-6 rounded-2xl border border-slate-800 bg-slate-950/60 p-4 sm:p-6"
    >
      <ErrorBanner message={error} />

      <section>
        <h3 className="text-sm font-semibold text-slate-100">
          Budget and usage
        </h3>
        <p className="text-xs text-slate-400">
          Tell us how much you&apos;d like to spend and how you mainly use your phone.
        </p>

        <div className="mt-4 grid gap-4 sm:grid-cols-2">
          <div>
            <label className="flex items-center justify-between text-xs text-slate-300">
              <span>Max budget (INR)</span>
              <span className="font-semibold text-emerald-400">
                {maxBudget?.toLocaleString("en-IN") ?? "No limit"}
              </span>
            </label>
            <input
              type="range"
              min={8000}
              max={80000}
              step={2000}
              value={maxBudget ?? 80000}
              onChange={e => setMaxBudget(Number(e.target.value))}
              className="mt-2 h-1.5 w-full cursor-pointer rounded-full bg-slate-800 accent-brand"
            />
          </div>

          <div>
            <label className="text-xs text-slate-300">
              Primary usage
            </label>
            <div className="mt-2 grid grid-cols-3 gap-2 text-[11px]">
              {["normal", "gaming", "photography"].map(value => (
                <button
                  key={value}
                  type="button"
                  onClick={() => setPrimaryUse(value)}
                  className={`rounded-lg border px-2 py-1.5 capitalize ${
                    primaryUse === value
                      ? "border-brand bg-brand/20 text-brand"
                      : "border-slate-700 bg-slate-900/60 text-slate-200 hover:border-brand/60"
                  }`}
                >
                  {value}
                </button>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section>
        <h3 className="text-sm font-semibold text-slate-100">
          Hardware priorities
        </h3>
        <p className="text-xs text-slate-400">
          Use the sliders to tell us what matters most.
        </p>

        <div className="mt-4 grid gap-4 sm:grid-cols-2">
          <PrioritySlider
            label="Camera quality"
            value={cameraPriority}
            onChange={setCameraPriority}
          />
          <PrioritySlider
            label="Battery life"
            value={batteryPriority}
            onChange={setBatteryPriority}
          />
          <PrioritySlider
            label="Performance (gaming)"
            value={performancePriority}
            onChange={setPerformancePriority}
          />
          <PrioritySlider
            label="Storage capacity"
            value={storagePriority}
            onChange={setStoragePriority}
          />
          <PrioritySlider
            label="RAM / multitasking"
            value={ramPriority}
            onChange={setRamPriority}
          />
        </div>
      </section>

      <section>
        <h3 className="text-sm font-semibold text-slate-100">
          Minimum specs and OS
        </h3>
        <div className="mt-4 grid gap-4 sm:grid-cols-3">
          <div>
            <label className="text-xs text-slate-300">Minimum RAM (GB)</label>
            <select
              value={minRam ?? ""}
              onChange={e =>
                setMinRam(e.target.value ? Number(e.target.value) : undefined)
              }
              className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-900/70 px-2 py-1.5 text-xs text-slate-100"
            >
              <option value="">No minimum</option>
              {[4, 6, 8, 12].map(v => (
                <option key={v} value={v}>
                  {v} GB
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-xs text-slate-300">
              Minimum storage (GB)
            </label>
            <select
              value={minStorage ?? ""}
              onChange={e =>
                setMinStorage(
                  e.target.value ? Number(e.target.value) : undefined
                )
              }
              className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-900/70 px-2 py-1.5 text-xs text-slate-100"
            >
              <option value="">No minimum</option>
              {[64, 128, 256, 512].map(v => (
                <option key={v} value={v}>
                  {v} GB
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-xs text-slate-300">OS preference</label>
            <div className="mt-1 flex gap-2 text-[11px]">
              {["Android", "iOS"].map(os => (
                <button
                  key={os}
                  type="button"
                  onClick={() =>
                    setOsPreference(prev => (prev === os ? undefined : os))
                  }
                  className={`flex-1 rounded-lg border px-2 py-1.5 ${
                    osPreference === os
                      ? "border-brand bg-brand/20 text-brand"
                      : "border-slate-700 bg-slate-900/60 text-slate-200 hover:border-brand/60"
                  }`}
                >
                  {os}
                </button>
              ))}
            </div>
          </div>
        </div>
      </section>

      <div className="flex items-center justify-between pt-2">
        <p className="text-[11px] text-slate-500">
          We score each phone based on your weights and explain{" "}
          <span className="font-medium text-slate-300">why it&apos;s a fit</span>.
        </p>
        <button
          type="submit"
          disabled={loading}
          className="inline-flex items-center gap-2 rounded-full bg-gradient-to-r from-brand to-brand-dark px-4 py-2 text-xs font-semibold text-white shadow-lg shadow-brand/30 hover:brightness-110 disabled:opacity-60"
        >
          {loading ? (
            <>
              <span className="h-3 w-3 animate-spin rounded-full border border-white border-t-transparent" />
              Calculating
            </>
          ) : (
            "See my matches"
          )}
        </button>
      </div>

      {loading && <LoadingSpinner />}
    </form>
  );
}

interface SliderProps {
  label: string;
  value: number;
  onChange: (v: number) => void;
}

function PrioritySlider({ label, value, onChange }: SliderProps) {
  return (
    <div>
      <div className="flex items-center justify-between text-xs text-slate-300">
        <span>{label}</span>
        <span className="text-[11px] text-slate-400">
          Priority: <span className="font-semibold">{value}</span>
        </span>
      </div>
      <input
        type="range"
        min={0}
        max={100}
        step={5}
        value={value}
        onChange={e => onChange(Number(e.target.value))}
        className="mt-2 h-1.5 w-full cursor-pointer rounded-full bg-slate-800 accent-brand"
      />
    </div>
  );
}

