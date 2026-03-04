import { useNavigate } from "react-router-dom";
import Layout from "../components/Layout";
import PreferenceForm from "../components/PreferenceForm";
import type {
  RecommendationRequest,
  RecommendationResponse
} from "../types";

export default function Preferences() {
  const navigate = useNavigate();

  const handleRecommendations = (
    data: RecommendationResponse,
    request: RecommendationRequest
  ) => {
    navigate("/results", {
      state: {
        recommendations: data.recommendations,
        request
      }
    });
  };

  return (
    <Layout>
      <div className="mb-6 max-w-2xl">
        <h2 className="text-xl font-semibold text-slate-50">
          Tell us what matters to you
        </h2>
        <p className="mt-1 text-xs text-slate-400">
          We&apos;ll use these preferences to score phones on battery, camera,
          performance, and value for money.
        </p>
      </div>
      <PreferenceForm onRecommendations={handleRecommendations} />
    </Layout>
  );
}

