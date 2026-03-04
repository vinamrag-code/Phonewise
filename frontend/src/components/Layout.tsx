import { Link, NavLink } from "react-router-dom";
import ThemeToggle from "./ThemeToggle";

interface Props {
  children: React.ReactNode;
}

export default function Layout({ children }: Props) {
  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-950 via-slate-950 to-slate-900 text-slate-50">
      <header className="sticky top-0 z-20 border-b border-slate-800 bg-slate-950/80 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
          <Link to="/" className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-brand to-brand-dark text-sm font-bold text-white shadow-lg">
              PW
            </div>
            <div className="flex flex-col leading-tight">
              <span className="text-sm font-semibold tracking-tight">
                PhoneWise
              </span>
              <span className="text-[11px] text-slate-400">
                Smart phone recommender
              </span>
            </div>
          </Link>

          <nav className="flex items-center gap-4 text-xs sm:text-sm">
            <NavLink
              to="/"
              className={({ isActive }) =>
                `hidden sm:inline-block hover:text-brand ${
                  isActive ? "text-brand" : "text-slate-300"
                }`
              }
            >
              Home
            </NavLink>
            <NavLink
              to="/preferences"
              className={({ isActive }) =>
                `hidden sm:inline-block hover:text-brand ${
                  isActive ? "text-brand" : "text-slate-300"
                }`
              }
            >
              Get recommendations
            </NavLink>
            <NavLink
              to="/compare"
              className={({ isActive }) =>
                `hidden sm:inline-block hover:text-brand ${
                  isActive ? "text-brand" : "text-slate-300"
                }`
              }
            >
              Compare
            </NavLink>
            <NavLink
              to="/admin"
              className={({ isActive }) =>
                `hidden md:inline-block hover:text-brand ${
                  isActive ? "text-brand" : "text-slate-500"
                }`
              }
            >
              Admin
            </NavLink>
            <ThemeToggle />
          </nav>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-4 py-6 sm:py-10">
        {children}
      </main>

      <footer className="border-t border-slate-800 bg-slate-950/80">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3 text-[11px] text-slate-500">
          <span>© {new Date().getFullYear()} PhoneWise</span>
          <span>Built for India • INR</span>
        </div>
      </footer>
    </div>
  );
}

