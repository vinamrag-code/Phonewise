export interface Phone {
  id?: string;
  name: string;
  price: number;
  battery: number;
  ram: number;
  storage: number;
  camera: number;
  chipset: string;
  os: string;
  country?: string;
  currency?: string;
}

export interface PhoneTag {
  key: string;
  label: string;
}

export interface RecommendationReason {
  title: string;
  detail: string;
}

export interface PhoneRecommendation {
  phone: Phone;
  match_score: number;
  match_percentage: number;
  reasons: RecommendationReason[];
  tags: PhoneTag[];
}

export interface RecommendationRequest {
  max_budget?: number | null;
  min_ram?: number | null;
  min_storage?: number | null;
  os_preference?: string | null;
  primary_use?: string | null;
  weights?: {
    budget: number;
    camera: number;
    battery: number;
    performance: number;
    storage: number;
    ram: number;
  } | null;
}

export interface RecommendationResponse {
  recommendations: PhoneRecommendation[];
}

