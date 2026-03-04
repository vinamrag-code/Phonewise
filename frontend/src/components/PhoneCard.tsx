import type { PhoneRecommendation } from "../types";
import TagPill from "./TagPill";
import RecommendationReason from "./RecommendationReason";

interface Props {
  rec: PhoneRecommendation;
  onToggleCompare?: (phoneId: string) => void;
  selectedForCompare?: boolean;
}

export default function PhoneCard({
  rec,
  onToggleCompare,
  selectedForCompare
}: Props) {
  const { phone } = rec;
  const priceLabel =
    phone.price && phone.price > 0
      ? `${phone.currency ?? "INR"} ${phone.price.toLocaleString("en-IN")}`
      : "Price not available";

  return (
    <article className="card flex flex-col gap-3 p-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="text-sm font-semibold text-slate-50">
            {phone.name}
          </h3>
          <p className="mt-1 text-xs text-slate-400">
            {phone.os} • {phone.chipset || "Chipset N/A"}
          </p>
        </div>
        <div className="flex flex-col items-end gap-1">
          <span className="text-xs text-slate-400">Match</span>
          <span className="text-lg font-semibold text-emerald-400">
            {rec.match_percentage}%
          </span>
          <span className="text-[11px] text-slate-500">{priceLabel}</span>
        </div>
      </div>

      <div className="mt-1 grid grid-cols-2 gap-2 text-[11px] text-slate-300 sm:grid-cols-4">
        <div className="rounded-lg bg-slate-900/70 px-2 py-1.5">
          <p className="text-slate-400">Battery</p>
          <p className="font-medium">{phone.battery || "N/A"} mAh</p>
        </div>
        <div className="rounded-lg bg-slate-900/70 px-2 py-1.5">
          <p className="text-slate-400">Camera</p>
          <p className="font-medium">{phone.camera || "N/A"} MP</p>
        </div>
        <div className="rounded-lg bg-slate-900/70 px-2 py-1.5">
          <p className="text-slate-400">Memory</p>
          <p className="font-medium">
            {phone.ram || "?"} GB • {phone.storage || "?"} GB
          </p>
        </div>
        <div className="rounded-lg bg-slate-900/70 px-2 py-1.5">
          <p className="text-slate-400">Region</p>
          <p className="font-medium">
            {phone.country ?? "Global"} / {phone.currency ?? "INR"}
          </p>
        </div>
      </div>

      {rec.tags && rec.tags.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1.5">
          {rec.tags.map(tag => (
            <TagPill key={tag.key} label={tag.label} />
          ))}
        </div>
      )}

      <RecommendationReason reasons={rec.reasons} />

      {onToggleCompare && phone.id && (
        <button
          type="button"
          onClick={() => onToggleCompare(phone.id!)}
          className={`mt-3 inline-flex items-center justify-center rounded-lg border px-3 py-1.5 text-xs font-medium ${
            selectedForCompare
              ? "border-emerald-500/60 bg-emerald-500/10 text-emerald-200"
              : "border-slate-700 bg-slate-900/60 text-slate-200 hover:border-emerald-500/60 hover:text-emerald-200"
          }`}
        >
          {selectedForCompare ? "Added to comparison" : "Add to comparison"}
        </button>
      )}
    </article>
  );
}

