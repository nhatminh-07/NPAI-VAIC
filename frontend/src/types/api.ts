// Định nghĩa kiểu dữ liệu (contract) dùng chung giữa frontend và backend cho mọi API.
// Mỗi khi backend đổi hình dạng response, cần cập nhật lại các interface tương ứng ở đây
// để TypeScript báo lỗi ngay tại các nơi frontend đang dùng sai dữ liệu.

// ---------- Kiểu dùng chung ----------

// Mức độ nghiêm trọng của bệnh trên cây - dùng cho cả kết quả chẩn đoán (mục 1)
// và báo cáo sâu bệnh của cán bộ (mục 4b).
export type Severity = 'healthy' | 'mild' | 'moderate' | 'severe';

export type RiskLevel = 'low' | 'medium' | 'high';

// 3 loại cây trồng mà hệ thống hỗ trợ. Nếu backend hỗ trợ thêm loại cây mới,
// phải thêm giá trị vào đây VÀ vào constants/crops.ts (danh sách hiển thị cho người dùng).
export type CropType = 'rice' | 'coffee' | 'vegetable';

export interface Crop {
  id: number;
  type: CropType;
  nameVi: string;
}

// ---------- 1. Nhận diện bệnh cây (trang /scan) ----------

export interface DiseaseDetectionResult {
  diseaseName: string;
  scientificName: string;
  confidence: number; // 0..1 - độ tin cậy của model, dưới 0.6 thì FE hiển thị cảnh báo
  severity: Severity;
  recommendations: string[]; // danh sách khuyến nghị xử lý, hiển thị dạng checklist
  imageUrl: string;
}

// ---------- 2. Dự báo năng suất & thời điểm thu hoạch (trang /forecast) ----------

export interface YieldInput {
  cropType: CropType;
  areaHa: number;
  plantingDate: string; // ISO date
  district: string;
}

// So sánh thời tiết hiện tại với điều kiện tối ưu cho loại cây đang trồng.
// Backend trả về nhưng trang /forecast hiện CHƯA hiển thị các trường này lên UI.
export interface WeatherComparison {
  current: {
    temperature: number;
    humidity: number;
    rainfall: number;
    description: string;
  };
  optimal: {
    temperature: string;
    humidity: string;
    rainfall: string;
  };
  deviation: {
    temperature: string;
    status: string;
  };
}

// Thông tin về giai đoạn sinh trưởng của cây trồng đang dự báo.
// Backend trả về nhưng trang /forecast hiện CHƯA hiển thị các trường này lên UI.
export interface CropInfo {
  name_vi: string;
  growth_days: number; // tổng số ngày sinh trưởng dự kiến của giống cây
  days_since_planting: number; // số ngày đã trồng tính đến thời điểm gọi API
  notes: string;
}

export interface YieldForecastResult {
  predictedYieldTPerHa: number;
  totalOutputTons: number;
  harvestWindowStart: string; // ISO date
  harvestWindowEnd: string; // ISO date
  confidence: number; // 0..1
  risk: RiskLevel;
  riskNote: string;
  rationale: string[]; // giải thích căn cứ đưa ra dự báo, hiển thị dạng danh sách

  // Các trường mở rộng (bổ sung sau bản đầu) - liên quan đến thời tiết/tiến độ sinh
  // trưởng thực tế. Kiểu đã khớp với response của backend nhưng UI /forecast hiện
  // chưa render các trường này (còn lại cho phiên bản sau).
  currentWeather: CurrentWeather;
  weatherComparison: WeatherComparison;
  harvestAdvice: 'optimal' | 'normal' | 'prepare_harvest' | 'harvest_early' | 'monitor';
  harvestAdviceNote: string;
  remainingDays: number; // số ngày còn lại ước tính đến thời điểm nên thu hoạch
  cropInfo: CropInfo;
}

// ---------- 3. Giá thị trường (trang /prices) ----------

export interface PriceHistoryPoint {
  date: string; // ISO date
  price: number; // VND per unit
}

export interface PriceForecastPoint {
  date: string; // ISO date
  price: number; // VND per unit
  lowerBand: number; // cận dưới khoảng dự báo, dùng vẽ dải tin cậy trên biểu đồ
  upperBand: number; // cận trên khoảng dự báo
}

export interface MarketPriceResult {
  cropId: number;
  cropName: string;
  unit: string; // vd "VND/kg"
  history: PriceHistoryPoint[]; // giá lịch sử (đường liền nét trên biểu đồ)
  forecast: PriceForecastPoint[]; // giá dự báo (đường đứt nét + dải tin cậy)
  currentPrice: number;
  change7dPercent: number;
  trendLabel: string; // tiếng Việt, trung lập (không phải khuyến nghị mua/bán)
}

// ---------- 4. Dashboard so sánh theo kỳ (trang /dashboard, dành cho cán bộ) ----------

export interface KpiValue {
  id: string;
  labelVi: string;
  value: number;
  unit: string;
  qoqDeltaPercent: number; // % thay đổi so với quý trước (quarter-over-quarter)
  yoyDeltaPercent: number; // % thay đổi so với cùng kỳ năm trước (year-over-year)
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
  period: string; // vd "2026-Q3", khớp với QuarterOption.value ở constants/periods.ts
  cropId?: number; // undefined nghĩa là lọc "tất cả cây trồng"
  kpis: KpiValue[];
  districtYield: DistrictYield[];
  diseaseCases: DiseaseCaseCount[];
  diseaseTrend: DiseaseTrendPoint[];
  districtRankings: DistrictRanking[];
}

// ---------- 4b. Báo cáo sâu bệnh (trang /disease-report, dành cho cán bộ) ----------
// Danh sách các lượt chẩn đoán/báo cáo sâu bệnh (mỗi lượt nông dân dùng trang /scan sẽ
// tạo ra 1 bản ghi ở đây). Xem chi tiết API contract tại getDiseaseReport() trong lib/api.ts.

export interface DiseaseReportEntry {
  id: number;
  district: string;
  cropType: CropType;
  diseaseName: string;
  severity: Severity;
  affectedPlantCount: number; // số cây bị ảnh hưởng, nông dân tự nhập khi báo cáo
  reportedAt: string; // ISO date
}

export interface DiseaseReportResult {
  reports: DiseaseReportEntry[];
}

// ---------- 5. Gợi ý cây trồng (crop recommendation) ----------

export interface CropRecommendationResult {
  recommendedCrop: string;
  cropNameVi: string;
  season: string;
  duration: string;
  expectedYield: string;
  tips: string;
  confidence: number;
}

// ---------- 6. Thời tiết ----------

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

// ---------- 7. Trợ lý AI (chatbot) ----------
// Xem chú thích chi tiết cho backend engineer tại hàm sendChatMessage() trong src/lib/api.ts

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface ChatResponse {
  reply: string; // câu trả lời của trợ lý AI, dạng văn bản tiếng Việt, sẵn sàng hiển thị trực tiếp
}
