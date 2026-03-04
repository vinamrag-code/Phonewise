import { useState } from "react";
import Layout from "../components/Layout";
import ErrorBanner from "../components/ErrorBanner";
import LoadingSpinner from "../components/LoadingSpinner";
import { triggerDatabaseUpdate, fetchPhones } from "../lib/api";

export default function Admin() {
  const [apiToken, setApiToken] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [phoneCount, setPhoneCount] = useState<number | null>(null);

  const handleRunScraper = async () => {
    setError("");
    setMessage("");
    if (!apiToken) {
      setError("Please enter the API secret token from your backend .env.");
      return;
    }
    setLoading(true);
    try {
      const res = await triggerDatabaseUpdate(apiToken);
      setMessage(
        `Scraper finished. Upserted or refreshed ${res.updated_count} phones.`
      );
    } catch (err) {
      setError(
        "Failed to trigger update. Check the token and make sure the backend is running."
      );
    } finally {
      setLoading(false);
    }
  };

  const handleRefreshCount = async () => {
    setError("");
    try {
      const phones = await fetchPhones();
      setPhoneCount(phones.length);
    } catch (err) {
      setError("Could not fetch current phone count.");
    }
  };

  return (
    <Layout>
      <div className="mb-4 max-w-2xl">
        <h2 className="text-xl font-semibold text-slate-50">
          Admin • Data refresh
        </h2>
        <p className="mt-1 text-xs text-slate-400">
          Trigger a fresh scrape from PhoneDB and inspect the current size of
          your local catalog.
        </p>
      </div>

      <div className="max-w-xl space-y-4 rounded-2xl border border-slate-800 bg-slate-950/60 p-4 sm:p-6">
        <ErrorBanner message={error} />
        {message && (
          <div className="mb-2 rounded-lg border border-emerald-500/40 bg-emerald-500/10 px-3 py-2 text-xs text-emerald-200">
            {message}
          </div>
        )}

        <div>
          <label className="text-xs text-slate-300">
            API secret token (backend `API_SECRET_TOKEN`)
          </label>
          <input
            type="password"
            value={apiToken}
            onChange={e => setApiToken(e.target.value)}
            placeholder="change-me"
            className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-900/80 px-3 py-2 text-xs text-slate-100"
          />
          <p className="mt-1 text-[11px] text-slate-500">
            This protects the `/update-database` endpoint from public access.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <button
            type="button"
            onClick={handleRunScraper}
            disabled={loading}
            className="inline-flex items-center gap-2 rounded-full bg-gradient-to-r from-brand to-brand-dark px-4 py-2 text-xs font-semibold text-white shadow-lg shadow-brand/30 hover:brightness-110 disabled:opacity-60"
          >
            Run scraper now
          </button>
          <button
            type="button"
            onClick={handleRefreshCount}
            className="text-xs font-medium text-slate-300 hover:text-brand"
          >
            Refresh phone count
          </button>
          {phoneCount !== null && (
            <span className="rounded-full bg-slate-900/70 px-3 py-1 text-[11px] text-slate-300">
              Current catalog:{" "}
              <span className="font-semibold text-slate-50">
                {phoneCount} phones
              </span>
            </span>
          )}
        </div>

        {loading && <LoadingSpinner />}
      </div>
    </Layout>
  );
}

