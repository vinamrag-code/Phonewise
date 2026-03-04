import { useLocation } from "react-router-dom";
import Layout from "../components/Layout";
import ComparisonTable from "../components/ComparisonTable";
import type { Phone } from "../types";

interface LocationState {
  phones?: Phone[];
}

export default function Compare() {
  const location = useLocation();
  const state = (location.state || {}) as LocationState;
  const phones = state.phones ?? [];

  return (
    <Layout>
      <div className="mb-4 max-w-2xl">
        <h2 className="text-xl font-semibold text-slate-50">
          Compare phones side by side
        </h2>
        <p className="mt-1 text-xs text-slate-400">
          We highlight the key hardware differences so you can make the final
          call confidently.
        </p>
      </div>
      <ComparisonTable phones={phones} />
    </Layout>
  );
}

