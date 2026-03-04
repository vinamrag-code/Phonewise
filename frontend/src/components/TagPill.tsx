interface Props {
  label: string;
}

export default function TagPill({ label }: Props) {
  return (
    <span className="inline-flex items-center rounded-full bg-emerald-500/10 px-2 py-0.5 text-[11px] font-medium text-emerald-300 ring-1 ring-emerald-500/40">
      {label}
    </span>
  );
}

