import type { RecommendationReason as Reason } from "../types";

interface Props {
  reasons: Reason[];
}

export default function RecommendationReason({ reasons }: Props) {
  if (!reasons || reasons.length === 0) return null;
  return (
    <ul className="mt-2 space-y-1 text-xs text-slate-300">
      {reasons.map((r, idx) => (
        <li key={idx} className="flex gap-2">
          <span className="mt-1 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-brand" />
          <div>
            <p className="font-medium text-slate-100">{r.title}</p>
            <p className="text-[11px] text-slate-400">{r.detail}</p>
          </div>
        </li>
      ))}
    </ul>
  );
}

