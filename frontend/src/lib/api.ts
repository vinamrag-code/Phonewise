import axios from "axios";
import type {
  RecommendationRequest,
  RecommendationResponse,
  Phone
} from "../types";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000
});

export async function fetchPhones(): Promise<Phone[]> {
  const res = await api.get<Phone[]>("/phones");
  return res.data;
}

export async function fetchRecommendations(
  payload: RecommendationRequest
): Promise<RecommendationResponse> {
  const res = await api.post<RecommendationResponse>("/recommend", payload);
  return res.data;
}

export async function triggerDatabaseUpdate(
  apiToken: string
): Promise<{ status: string; updated_count: number }> {
  const res = await api.post<{ status: string; updated_count: number }>(
    "/update-database",
    null,
    { params: { api_token: apiToken } }
  );
  return res.data;
}

