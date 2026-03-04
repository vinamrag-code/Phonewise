import { Link } from "react-router-dom";
import Layout from "../components/Layout";

export default function Landing() {
  return (
    <Layout>
      <section className="grid gap-8 md:grid-cols-[1.3fr,1fr] md:items-center">
        <div>
          <h1 className="bg-gradient-to-br from-slate-50 via-sky-200 to-emerald-300 bg-clip-text text-3xl font-semibold tracking-tight text-transparent sm:text-4xl md:text-5xl">
            Find the right phone,
            <br />
            not just the latest one.
          </h1>
          <p className="mt-4 max-w-xl text-sm text-slate-300">
            PhoneWise analyzes real hardware specs — battery, camera, RAM,
            storage, and chipset — against your budget and priorities to
            recommend phones that actually fit your life in India.
          </p>

          <div className="mt-6 flex flex-wrap items-center gap-3">
            <Link
              to="/preferences"
              className="inline-flex items-center gap-2 rounded-full bg-gradient-to-r from-brand to-brand-dark px-5 py-2.5 text-sm font-semibold text-white shadow-lg shadow-brand/40 hover:brightness-110"
            >
              Start in 30 seconds
              <span aria-hidden="true">→</span>
            </Link>
            <Link
              to="/compare"
              className="text-xs font-medium text-slate-300 hover:text-brand"
            >
              Or compare models manually
            </Link>
          </div>

          <dl className="mt-8 grid grid-cols-3 gap-4 text-[11px] text-slate-400 sm:max-w-md">
            <div className="rounded-xl border border-slate-800 bg-slate-950/60 px-3 py-2">
              <dt className="text-slate-400">Optimized for India</dt>
              <dd className="mt-1 text-slate-200">Specs tuned for INR budgets</dd>
            </div>
            <div className="rounded-xl border border-slate-800 bg-slate-950/60 px-3 py-2">
              <dt className="text-slate-400">Spec-aware engine</dt>
              <dd className="mt-1 text-slate-200">Battery, camera, gaming, OS</dd>
            </div>
            <div className="rounded-xl border border-slate-800 bg-slate-950/60 px-3 py-2">
              <dt className="text-slate-400">Explainable picks</dt>
              <dd className="mt-1 text-slate-200">
                See why each phone is chosen
              </dd>
            </div>
          </dl>
        </div>

        <div className="card relative overflow-hidden">
          <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_10%_0,rgba(56,189,248,0.35),transparent_55%),radial-gradient(circle_at_90%_100%,rgba(129,140,248,0.4),transparent_55%)] opacity-80" />
          <div className="relative space-y-4 p-5 text-xs text-slate-100">
            <p className="text-[11px] uppercase tracking-[0.2em] text-slate-300">
              Live preview
            </p>
            <p className="text-sm text-slate-200">
              &ldquo;Show me Android phones under{" "}
              <span className="font-semibold text-emerald-300">
                ₹30,000
              </span>{" "}
              with great{" "}
              <span className="font-semibold text-emerald-300">
                battery
              </span>{" "}
              and{" "}
              <span className="font-semibold text-emerald-300">
                camera
              </span>
              .&rdquo;
            </p>
            <div className="mt-3 space-y-2 rounded-xl bg-slate-950/70 p-3">
              <div className="flex items-center justify-between text-[11px] text-slate-300">
                <span>Top match</span>
                <span className="rounded-full bg-emerald-500/10 px-2 py-0.5 text-[10px] font-semibold text-emerald-300 ring-1 ring-emerald-500/40">
                  92% match
                </span>
              </div>
              <p className="text-sm font-semibold">
                Samsung Galaxy A07 5G (example)
              </p>
              <ul className="mt-1 space-y-1 text-[11px] text-slate-200">
                <li>• 6000 mAh battery lasts all day</li>
                <li>• 50 MP main camera with HDR</li>
                <li>• Dimensity 6300 tuned for everyday gaming</li>
              </ul>
            </div>
            <p className="mt-2 text-[11px] text-slate-400">
              Backed by a real database of device specs — not ad-driven
              affiliate lists.
            </p>
          </div>
        </div>
      </section>
    </Layout>
  );
}

