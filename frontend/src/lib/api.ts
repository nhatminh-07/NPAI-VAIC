import type {
  ChatMessage,
  ChatResponse,
  CropType,
  DashboardResult,
  DiseaseDetectionResult,
  DiseaseReportResult,
  FarmingPeriod,
  FarmingPeriodListResult,
  FarmingRegion,
  FarmingRegionListResult,
  MarketPriceResult,
  YieldForecastResult,
  YieldInput,
  CropRecommendationResult,
  CurrentWeather,
  WeatherForecastResult,
} from '@/types/api';

// Module DUY NHẤT của frontend biết chi tiết giao tiếp với backend (base URL, phương
// thức HTTP, hình dạng lỗi trả về). Các trang (page) không bao giờ gọi fetch() trực
// tiếp - chỉ gọi các hàm export ở file này. Nhờ vậy khi backend đổi endpoint/contract,
// chỉ cần sửa ở đây, không phải sửa rải rác trong từng trang.

// Ưu tiên biến môi trường NEXT_PUBLIC_API_BASE_URL (hoặc NEXT_PUBLIC_API_URL cũ),
// fallback về localhost:8000 khi chạy dev mà chưa cấu hình .env.local.
const API_BASE_URL = (process.env.NEXT_PUBLIC_API_BASE_URL ?? process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000').replace(/\/$/, '');

export class ApiError extends Error {
  /** true khi request không tới được server (mất mạng/DNS lỗi/CORS chặn...),
   * false khi server có phản hồi nhưng trả về status lỗi (4xx/5xx).
   * Các trang dùng cờ này để phân biệt "chưa kết nối được máy chủ" và "lỗi khác". */
  offline: boolean;

  constructor(message: string, offline: boolean) {
    super(message);
    this.name = 'ApiError';
    this.offline = offline;
  }
}

// Hàm fetch dùng chung cho mọi API call bên dưới: tự thêm base URL, tự bắt lỗi mạng
// và lỗi HTTP status rồi quy về cùng 1 kiểu ApiError để các trang xử lý thống nhất.
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

// Gửi ảnh + thông tin kèm theo để backend chẩn đoán bệnh cây (trang /scan).
// Dùng multipart/form-data vì có kèm file ảnh.
// `regionId` tuỳ chọn: vùng canh tác (do cán bộ tạo, xem farming_regions) mà cây bị
// bệnh này thuộc về - GHI CHÚ CHO BACKEND: đây là field MỚI, hiện `/disease/detect`
// chưa nhận field này, cần thêm 1 Form field tuỳ chọn `regionId: Optional[int]` và lưu
// vào `DiseaseDetection.farming_region_id` (nullable, để tương thích ngược với báo cáo
// không chọn vùng). Không bắt buộc điền vì farmer có thể chưa có vùng canh tác nào.
export async function detectDisease(
  file: File,
  cropType: CropType,
  affectedPlantCount: number,
  regionId?: number,
): Promise<DiseaseDetectionResult> {
  const formData = new FormData();
  formData.append('image', file);
  formData.append('cropType', cropType);
  formData.append('affectedPlantCount', String(affectedPlantCount));
  if (regionId !== undefined) formData.append('regionId', String(regionId));
  return request<DiseaseDetectionResult>('/disease/detect', {
    method: 'POST',
    body: formData,
  });
}

// Lấy danh sách báo cáo sâu bệnh cho trang /disease-report (cán bộ nông nghiệp).
// Kiểu `raw` khai báo mọi field là optional (`?`) vì không chắc backend luôn trả đủ
// - nếu thiếu field `reports`, ta coi như danh sách rỗng (`?? []`) thay vì throw lỗi.
export async function getDiseaseReport(): Promise<DiseaseReportResult> {
  const raw = await request<{
    reports?: Array<{
      id: number;
      district: string;
      cropType: DiseaseReportResult['reports'][number]['cropType'];
      diseaseName: string;
      severity: DiseaseReportResult['reports'][number]['severity'];
      affectedPlantCount: number;
      reportedAt: string;
    }>;
  }>('/disease-report');

  return { reports: raw.reports ?? [] };
}

// Dự báo năng suất & thời điểm thu hoạch (trang /forecast).
export async function predictYield(input: YieldInput): Promise<YieldForecastResult> {
  return request<YieldForecastResult>('/yield/predict', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  });
}

// Lấy giá thị trường (lịch sử + dự báo) cho 1 loại cây trồng (trang /prices).
export async function getMarketPrice(cropId: number): Promise<MarketPriceResult> {
  const params = new URLSearchParams({ cropId: String(cropId) });
  return request<MarketPriceResult>(`/market/price?${params.toString()}`);
}

// Lấy dữ liệu tổng hợp cho dashboard cán bộ (trang /dashboard), theo kỳ báo cáo
// (quý/năm) và tuỳ chọn lọc theo 1 loại cây trồng cụ thể.
// Cũng như getDiseaseReport(), mọi field trong `raw` là optional để phòng backend
// trả thiếu - khi đó FE tự điền mảng rỗng thay vì crash khi render (`?? []`).
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

// N/P/K = hàm lượng Đạm/Lân/Kali trong đất (đơn vị theo chuẩn backend, thường là mg/kg),
// ph = độ pH đất. Dùng cho tính năng gợi ý cây trồng phù hợp dựa trên điều kiện đất/khí hậu.
export interface CropRecommendInput {
  N: number;
  P: number;
  K: number;
  temperature: number;
  humidity: number;
  ph: number;
  rainfall: number;
}

// Gợi ý loại cây trồng phù hợp dựa trên thông số đất + khí hậu đầu vào.
// Response backend bọc trong { success, data } - hàm này chỉ trả về phần `data`
// cho gọn, các trang gọi hàm không cần quan tâm field `success`.
export async function recommendCrop(input: CropRecommendInput): Promise<CropRecommendationResult> {
  const res = await request<{ success: boolean; data: CropRecommendationResult }>('/crop/recommend', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  });
  return res.data;
}

// Lấy thời tiết hiện tại. lat/lon để trống thì backend tự dùng toạ độ mặc định
// (khu vực Điện Biên).
export async function getCurrentWeather(lat?: number, lon?: number): Promise<CurrentWeather> {
  const params = new URLSearchParams();
  if (lat !== undefined) params.set('lat', String(lat));
  if (lon !== undefined) params.set('lon', String(lon));
  const query = params.toString();
  const res = await request<{ success: boolean; data: CurrentWeather }>(`/weather/current${query ? '?' + query : ''}`);
  return res.data;
}

// Lấy dự báo thời tiết nhiều ngày tới, cùng quy ước lat/lon như getCurrentWeather().
export async function getWeatherForecast(lat?: number, lon?: number): Promise<WeatherForecastResult> {
  const params = new URLSearchParams();
  if (lat !== undefined) params.set('lat', String(lat));
  if (lon !== undefined) params.set('lon', String(lon));
  const query = params.toString();
  const res = await request<{ success: boolean; data: WeatherForecastResult }>(`/weather/forecast${query ? '?' + query : ''}`);
  return res.data;
}

/**
 * GHI CHÚ CHO BACKEND ENGINEER (trợ lý AI / chatbot):
 * ----------------------------------------------------
 * Frontend gọi endpoint này mỗi khi người dùng gửi 1 tin nhắn trong khung chat
 * (component ChatWidget). Backend cần implement:
 *
 *   POST /assistant/chat
 *
 * Request body (JSON):
 *   {
 *     "message": string,          // câu hỏi mới nhất của người dùng, vd:
 *                                  // "Tóm tắt những sự kiện trong quý 3 năm 2025"
 *     "history": [                // (tuỳ chọn) các lượt hỏi/đáp trước đó trong CÙNG
 *       { "role": "user" | "assistant", "content": string },   // phiên chat, để backend
 *       ...                                                     // hiểu ngữ cảnh hội thoại
 *     ]
 *   }
 *
 * Response body (JSON), status 200:
 *   {
 *     "reply": string   // câu trả lời bằng tiếng Việt, dạng văn bản thuần (frontend hiển
 *                        // thị nguyên văn, không parse Markdown/HTML)
 *   }
 *
 * Lỗi: trả về HTTP status khác 2xx kèm body bất kỳ là đủ - frontend chỉ hiển thị
 * thông báo lỗi chung, không đọc chi tiết message lỗi từ backend.
 *
 * Gợi ý xử lý cho câu như "Tóm tắt những sự kiện trong quý X năm Y":
 * backend cần tự phân tích message để lấy quý/năm, sau đó truy vấn các bảng liên quan
 * (disease_detections, yield_predictions, market_prices...) trong khoảng thời gian đó rồi
 * tổng hợp/diễn giải thành đoạn văn (có thể dùng LLM hoặc rule-based). Frontend không gửi
 * kèm bất kỳ dữ liệu tổng hợp nào - toàn bộ việc truy vấn + suy luận là trách nhiệm backend.
 */
export async function sendChatMessage(message: string, history: ChatMessage[] = []): Promise<ChatResponse> {
  return request<ChatResponse>('/assistant/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, history }),
  });
}

/**
 * GHI CHÚ CHO BACKEND ENGINEER (Quản lý vùng canh tác & vụ canh tác):
 * ---------------------------------------------------------------------
 * 4 hàm bên dưới gọi 4 endpoint MỚI mà backend CHƯA có - cần implement:
 *
 *   POST /farming-regions   - cán bộ tạo 1 vùng canh tác (trang /management của cán bộ)
 *   GET  /farming-regions   - lấy danh sách vùng canh tác (dùng ở cả trang cán bộ và
 *                             dropdown chọn vùng ở trang /management của nông dân)
 *   POST /farming-periods   - nông dân khai báo 1 vụ canh tác, gắn với 1 vùng có sẵn
 *   GET  /farming-periods   - lấy danh sách vụ canh tác đã khai báo
 *
 * Request POST /farming-regions (JSON):
 *   { "name": string, "district": string, "areaHa": number }
 * Response (JSON), status 200 - trả về bản ghi vừa tạo:
 *   { "id": number, "name": string, "district": string, "areaHa": number, "createdAt": string (ISO date) }
 *
 * Response GET /farming-regions (JSON):
 *   { "regions": [ { id, name, district, areaHa, createdAt }, ... ] }
 *
 * Request POST /farming-periods (JSON):
 *   { "regionId": number, "cropType": "rice"|"coffee"|"vegetable", "areaHa": number, "cropCount": number }
 * Response (JSON), status 200 - trả về bản ghi vừa tạo (kèm regionName đã join sẵn):
 *   { "id": number, "regionId": number, "regionName": string, "cropType": string,
 *     "areaHa": number, "cropCount": number, "createdAt": string (ISO date) }
 *
 * Response GET /farming-periods (JSON):
 *   { "periods": [ { id, regionId, regionName, cropType, areaHa, cropCount, createdAt }, ... ] }
 *
 * Lưu ý: app hiện KHÔNG có đăng nhập/phân quyền thực sự (chỉ có màn chọn vai trò ở
 * trang chủ, không xác thực) - nên các endpoint này KHÔNG cần userId/token, cứ tạo/đọc
 * chung 1 danh sách cho tất cả người dùng, giống hệt cách /disease-report đang làm.
 * Xem thêm gợi ý thiết kế bảng ở models.py trong phần trao đổi riêng với backend engineer.
 */
export async function getFarmingRegions(): Promise<FarmingRegionListResult> {
  const raw = await request<{ regions?: FarmingRegion[] }>('/farming-regions');
  return { regions: raw.regions ?? [] };
}

export async function createFarmingRegion(input: { name: string; district: string; areaHa: number }): Promise<FarmingRegion> {
  return request<FarmingRegion>('/farming-regions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  });
}

// Xoá 1 vùng canh tác. Backend đồng thời xoá các vụ canh tác thuộc vùng và gỡ liên kết
// vùng khỏi báo cáo sâu bệnh (giữ lại bản ghi báo cáo). Trả về { ok: true }.
export async function deleteFarmingRegion(regionId: number): Promise<void> {
  await request<{ ok: boolean }>(`/farming-regions/${regionId}`, { method: 'DELETE' });
}

export async function getFarmingPeriods(): Promise<FarmingPeriodListResult> {
  const raw = await request<{ periods?: FarmingPeriod[] }>('/farming-periods');
  return { periods: raw.periods ?? [] };
}

export async function createFarmingPeriod(input: {
  regionId: number;
  cropType: CropType;
  areaHa: number;
  cropCount: number;
}): Promise<FarmingPeriod> {
  return request<FarmingPeriod>('/farming-periods', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  });
}

// Xoá 1 vụ canh tác (planting operation). Trả về { ok: true }.
export async function deleteFarmingPeriod(periodId: number): Promise<void> {
  await request<{ ok: boolean }>(`/farming-periods/${periodId}`, { method: 'DELETE' });
}
