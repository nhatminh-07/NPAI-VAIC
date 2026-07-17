import type {
  DashboardResult,
  DiseaseDetectionResult,
  MarketPriceResult,
  YieldForecastResult,
  YieldInput,
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
    crop_name?: string | null;
    total_area_ha?: { label: string; current: number; previous: number; change_percent: number };
    avg_yield_per_ha?: { label: string; current: number; previous: number; change_percent: number };
    disease_case_count?: { label: string; current: number; previous: number; change_percent: number };
    disease_rate_percent?: { label: string; current: number; previous: number; change_percent: number };
    year_over_year_note?: string;
  }>(`/dashboard?${params.toString()}`);

  const kpis = [
    raw.total_area_ha && {
      id: 'total_area_ha',
      labelVi: raw.total_area_ha.label || 'Tổng diện tích',
      value: raw.total_area_ha.current,
      unit: 'ha',
      qoqDeltaPercent: raw.total_area_ha.change_percent,
      yoyDeltaPercent: 0,
    },
    raw.avg_yield_per_ha && {
      id: 'avg_yield_per_ha',
      labelVi: raw.avg_yield_per_ha.label || 'Năng suất trung bình',
      value: raw.avg_yield_per_ha.current,
      unit: 'tấn/ha',
      qoqDeltaPercent: raw.avg_yield_per_ha.change_percent,
      yoyDeltaPercent: 0,
    },
    raw.disease_case_count && {
      id: 'disease_case_count',
      labelVi: raw.disease_case_count.label || 'Số ca sâu bệnh',
      value: raw.disease_case_count.current,
      unit: 'ca',
      qoqDeltaPercent: raw.disease_case_count.change_percent,
      yoyDeltaPercent: 0,
    },
    raw.disease_rate_percent && {
      id: 'disease_rate_percent',
      labelVi: raw.disease_rate_percent.label || 'Tỷ lệ sâu bệnh',
      value: raw.disease_rate_percent.current,
      unit: '%',
      qoqDeltaPercent: raw.disease_rate_percent.change_percent,
      yoyDeltaPercent: 0,
    },
  ].filter(Boolean) as DashboardResult['kpis'];

  return {
    period: raw.period,
    cropId: cropId,
    kpis,
    districtYield: [],
    diseaseCases: [],
    diseaseTrend: [],
    districtRankings: [],
  };
}
