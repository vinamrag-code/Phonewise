import type { Phone } from "../types";

interface Props {
  phones: Phone[];
}

export default function ComparisonTable({ phones }: Props) {
  if (!phones.length) {
    return (
      <p className="text-sm text-slate-400">
        Select phones from the results page to compare them side by side.
      </p>
    );
  }

  return (
    <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-950/60">
      <table className="min-w-full text-left text-xs text-slate-200">
        <thead>
          <tr>
            <th className="px-3 py-3 text-slate-400">Spec</th>
            {phones.map(p => (
              <th key={p.id ?? p.name} className="px-3 py-3 font-semibold">
                {p.name}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-800">
          <ComparisonRow
            label="OS / Chipset"
            values={phones.map(
              p =>
                `${p.os || "N/A"} • ${
                  p.chipset.length > 40
                    ? p.chipset.slice(0, 37) + "..."
                    : p.chipset || "N/A"
                }`
            )}
          />
          <ComparisonRow
            label="Battery"
            values={phones.map(p => (p.battery ? `${p.battery} mAh` : "N/A"))}
          />
          <ComparisonRow
            label="Camera"
            values={phones.map(p => (p.camera ? `${p.camera} MP` : "N/A"))}
          />
          <ComparisonRow
            label="Memory"
            values={phones.map(
              p =>
                `${p.ram || "?"} GB RAM • ${p.storage || "?"} GB storage`
            )}
          />
          <ComparisonRow
            label="Price"
            values={phones.map(p =>
              p.price && p.price > 0
                ? `${p.currency ?? "INR"} ${p.price.toLocaleString("en-IN")}`
                : "N/A"
            )}
          />
        </tbody>
      </table>
    </div>
  );
}

interface RowProps {
  label: string;
  values: string[];
}

function ComparisonRow({ label, values }: RowProps) {
  return (
    <tr>
      <td className="whitespace-nowrap px-3 py-2 text-slate-400">{label}</td>
      {values.map((v, idx) => (
        <td key={idx} className="px-3 py-2">
          {v}
        </td>
      ))}
    </tr>
  );
}

