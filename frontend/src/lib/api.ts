import type {
  DashboardResult,
  DiseaseDetectionResult,
  MarketPriceResult,
  YieldForecastResult,
  YieldInput,
  CropRecommendationResult,
  CurrentWeather,
  WeatherForecastResult,
} from '@/types/api';

// The only module aware of the backend's transport details (base URL, HTTP
// verbs, error shape). Pages only ever call the functions exported here.

const API_BASE_URL = (process.env.NEXT_PUBLIC_API_BASE_URL ?? process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000').replace(/\/$/, '');

export class ApiError extends Error {
  /** true when the request never reached the server (network/DNS/CORS failure) */
  offline: boolean;

  constructor(message: string, offline: boolean) {
    super(message);
    this.name = 'ApiError';
    this.offline = offline;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE_URL}${path}`, init);
  } catch {
    throw new ApiError('Network request failed', true);
  }
  if (!res.ok) {
    throw new ApiError(`Request failed with status ${res.status}`, false);
  }
  return (await res.json()) as T;
}

export async function detectDisease(file: File): Promise<DiseaseDetectionResult> {
  const formData = new FormData();
  formData.append('image', file);
  return request<DiseaseDetectionResult>('/disease/detect', {
    method: 'POST',
    body: formData,
  });
}

export async function predictYield(input: YieldInput): Promise<YieldForecastResult> {
  return request<YieldForecastResult>('/yield/predict', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  });
}

export async function getMarketPrice(cropId: number): Promise<MarketPriceResult> {
  const params = new URLSearchParams({ cropId: String(cropId) });
  return request<MarketPriceResult>(`/market/price?${params.toString()}`);
}

export async function getDashboard(period: string, cropId?: number): Promise<DashboardResult> {
  const params = new URLSearchParams({ period });
  if (cropId !== undefined) params.set('cropId', String(cropId));

  const raw = await request<{
    period: string;
    cropId?: number;
    kpis?: Array<{
      id: string;
      labelVi: string;
      value: number;
      unit: string;
      qoqDeltaPercent: number;
      yoyDeltaPercent: number;
    }>;
    districtYield?: Array<{
      district: string;
      currentYieldTPerHa: number;
      previousYieldTPerHa: number;
    }>;
    diseaseCases?: Array<{
      diseaseName: string;
      cases: number;
    }>;
    diseaseTrend?: Array<{
      quarterLabel: string;
      cases: number;
    }>;
    districtRankings?: Array<{
      rank: number;
      district: string;
      yieldTPerHa: number;
      outputTons: number;
      diseaseCases: number;
    }>;
  }>(`/dashboard?${params.toString()}`);

  return {
    period: raw.period,
    cropId: cropId,
    kpis: raw.kpis ?? [],
    districtYield: raw.districtYield ?? [],
    diseaseCases: raw.diseaseCases ?? [],
    diseaseTrend: raw.diseaseTrend ?? [],
    districtRankings: raw.districtRankings ?? [],
  };
}

export interface CropRecommendInput {
  N: number;
  P: number;
  K: number;
  temperature: number;
  humidity: number;
  ph: number;
  rainfall: number;
}

export async function recommendCrop(input: CropRecommendInput): Promise<CropRecommendationResult> {
  const res = await request<{ success: boolean; data: CropRecommendationResult }>('/crop/recommend', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  });
  return res.data;
}

export async function getCurrentWeather(lat?: number, lon?: number): Promise<CurrentWeather> {
  const params = new URLSearchParams();
  if (lat !== undefined) params.set('lat', String(lat));
  if (lon !== undefined) params.set('lon', String(lon));
  const query = params.toString();
  const res = await request<{ success: boolean; data: CurrentWeather }>(`/weather/current${query ? '?' + query : ''}`);
  return res.data;
}

export async function getWeatherForecast(lat?: number, lon?: number): Promise<WeatherForecastResult> {
  const params = new URLSearchParams();
  if (lat !== undefined) params.set('lat', String(lat));
  if (lon !== undefined) params.set('lon', String(lon));
  const query = params.toString();
  const res = await request<{ success: boolean; data: WeatherForecastResult }>(`/weather/forecast${query ? '?' + query : ''}`);
  return res.data;
}
