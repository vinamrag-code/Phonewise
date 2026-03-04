import { useTheme } from "../hooks/useTheme";

export default function ThemeToggle() {
  const [theme, toggleTheme] = useTheme();

  return (
    <button
      type="button"
      onClick={toggleTheme}
      className="inline-flex items-center gap-2 rounded-full border border-slate-700 bg-slate-900/60 px-3 py-1 text-xs font-medium text-slate-200 shadow-sm hover:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-brand"
    >
      <span
        className="inline-block h-2 w-2 rounded-full"
        aria-hidden="true"
        style={{ backgroundColor: theme === "dark" ? "#22c55e" : "#eab308" }}
      />
      <span>{theme === "dark" ? "Dark" : "Light"} mode</span>
    </button>
  );
}

