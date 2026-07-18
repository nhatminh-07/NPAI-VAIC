// Shared API contract types. The frontend and (future) backend both implement this contract.

// ---------- Common ----------

export type Severity = 'healthy' | 'mild' | 'moderate' | 'severe';

export type RiskLevel = 'low' | 'medium' | 'high';

export type CropType = 'rice' | 'coffee' | 'vegetable';

export interface Crop {
  id: number;
  type: CropType;
  nameVi: string;
}

// ---------- 1. Disease detection ----------

export interface DiseaseDetectionResult {
  diseaseName: string;
  scientificName: string;
  confidence: number; // 0..1
  severity: Severity;
  recommendations: string[];
  imageUrl: string;
}

// ---------- 2. Yield & harvest-window forecast ----------

export interface YieldInput {
  cropType: CropType;
  areaHa: number;
  plantingDate: string; // ISO date
  district: string;
}

export interface YieldForecastResult {
  predictedYieldTPerHa: number;
  totalOutputTons: number;
  harvestWindowStart: string; // ISO date
  harvestWindowEnd: string; // ISO date
  confidence: number; // 0..1
  risk: RiskLevel;
  riskNote: string;
  rationale: string[];
}

// ---------- 3. Market price ----------

export interface PriceHistoryPoint {
  date: string; // ISO date
  price: number; // VND per unit
}

export interface PriceForecastPoint {
  date: string; // ISO date
  price: number; // VND per unit
  lowerBand: number;
  upperBand: number;
}

export interface MarketPriceResult {
  cropId: number;
  cropName: string;
  unit: string; // e.g. "VND/kg"
  history: PriceHistoryPoint[];
  forecast: PriceForecastPoint[];
  currentPrice: number;
  change7dPercent: number;
  trendLabel: string; // Vietnamese, neutral (no buy/sell advice)
}

// ---------- 4. Period-comparison dashboard ----------

export interface KpiValue {
  id: string;
  labelVi: string;
  value: number;
  unit: string;
  qoqDeltaPercent: number;
  yoyDeltaPercent: number;
}

export interface DistrictYield {
  district: string;
  currentYieldTPerHa: number;
  previousYieldTPerHa: number;
}

export interface DiseaseCaseCount {
  diseaseName: string;
  cases: number;
}

export interface DiseaseTrendPoint {
  quarterLabel: string;
  cases: number;
}

export interface DistrictRanking {
  rank: number;
  district: string;
  yieldTPerHa: number;
  outputTons: number;
  diseaseCases: number;
}

export interface DashboardResult {
  period: string;
  cropId?: number;
  kpis: KpiValue[];
  districtYield: DistrictYield[];
  diseaseCases: DiseaseCaseCount[];
  diseaseTrend: DiseaseTrendPoint[];
  districtRankings: DistrictRanking[];
}

// ---------- 4b. Disease/pest report (báo cáo sâu bệnh) ----------

export interface DiseaseReportEntry {
  id: number;
  district: string;
  cropType: CropType;
  diseaseName: string;
  severity: Severity;
  affectedPlantCount: number;
  reportedAt: string; // ISO date
}

export interface DiseaseReportResult {
  reports: DiseaseReportEntry[];
}

// ---------- 5. Crop recommendation ----------

export interface CropRecommendationResult {
  recommendedCrop: string;
  cropNameVi: string;
  season: string;
  duration: string;
  expectedYield: string;
  tips: string;
  confidence: number;
}

// ---------- 6. Weather ----------

export interface CurrentWeather {
  temperature: number;
  humidity: number;
  precipitation: number;
  windSpeed: number;
  soilTemperature: number;
  weatherDescription: string;
  weatherIcon: string;
  location: string;
}

export interface DailyForecast {
  date: string;
  weatherDescription: string;
  weatherIcon: string;
  tempMax: number;
  tempMin: number;
  precipitation: number;
  windMax: number;
}

export interface WeatherForecastResult {
  location: string;
  forecast: DailyForecast[];
}

// ---------- 7. AI Assistant (chatbot) ----------
// Xem chú thích chi tiết cho backend engineer tại hàm sendChatMessage() trong src/lib/api.ts

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface ChatResponse {
  reply: string; // câu trả lời của trợ lý AI, dạng văn bản tiếng Việt, sẵn sàng hiển thị trực tiếp
}
