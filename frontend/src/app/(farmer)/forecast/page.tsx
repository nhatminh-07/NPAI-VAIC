'use client';

import { useMemo, useState } from 'react';
import type { FormEvent } from 'react';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Select } from '@/components/ui/Select';
import { Badge } from '@/components/ui/Badge';
import type { BadgeTone } from '@/components/ui/Badge';
import { Spinner } from '@/components/ui/Spinner';
import { EmptyState } from '@/components/ui/EmptyState';
import { copy } from '@/constants/copy';
import { ApiError, predictYield } from '@/lib/api';
import { districts } from '@/constants/districts';
import type { CropType, RiskLevel, YieldForecastResult, YieldInput } from '@/types/api';

type Status = 'idle' | 'loading' | 'success' | 'error';

const riskTone: Record<RiskLevel, BadgeTone> = {
  low: 'good',
  medium: 'warning',
  high: 'critical',
};

const cropOptions: { value: CropType; label: string }[] = [
  { value: 'rice', label: copy.forecast.crop.rice },
  { value: 'coffee', label: copy.forecast.crop.coffee },
  { value: 'vegetable', label: copy.forecast.crop.vegetable },
];

// Định dạng ngày ISO (backend trả về) sang dạng tiếng Việt (dd/mm/yyyy) để hiển thị.
function formatDateVi(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleDateString('vi-VN');
}

// Trang dự báo năng suất & thời điểm thu hoạch: nông dân nhập thông tin vụ mùa (loại
// cây, diện tích, ngày gieo trồng, huyện), backend trả về năng suất/sản lượng dự kiến
// và cửa sổ thời gian nên thu hoạch.
// Lưu ý: YieldForecastResult (types/api.ts) có thêm các trường mở rộng về thời tiết
// (currentWeather, weatherComparison, harvestAdvice...) mà trang này CHƯA hiển thị -
// nếu cần bổ sung UI cho các trường đó thì bổ sung ở khối "status === 'success'" bên dưới.
export default function ForecastPage() {
  const [form, setForm] = useState<YieldInput>({
    cropType: 'rice',
    areaHa: 1,
    plantingDate: new Date().toISOString().slice(0, 10),
    district: districts[0],
  });
  const [touched, setTouched] = useState(false);
  const [status, setStatus] = useState<Status>('idle');
  const [result, setResult] = useState<YieldForecastResult | null>(null);
  const [offline, setOffline] = useState(false);

  // Validate form phía client TRƯỚC khi gọi API, để không tốn round-trip cho dữ liệu
  // rõ ràng sai. cropType/district luôn hợp lệ vì chọn từ dropdown, không cần validate.
  const errors = useMemo(() => {
    const e: { areaHa?: string; plantingDate?: string } = {};
    if (!(form.areaHa > 0)) e.areaHa = copy.forecast.areaError;
    if (!form.plantingDate) e.plantingDate = copy.forecast.plantingDateError;
    return e;
  }, [form.areaHa, form.plantingDate]);

  const isValid = Object.keys(errors).length === 0;

  async function runPrediction() {
    setStatus('loading');
    try {
      const res = await predictYield(form);
      setResult(res);
      setStatus('success');
    } catch (err) {
      setOffline(err instanceof ApiError && err.offline);
      setStatus('error');
    }
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setTouched(true);
    if (!isValid) return;
    void runPrediction();
  }

  return (
    <div className="mx-auto max-w-md px-4 py-5">
      <h1 className="mb-4 text-2xl font-bold text-ink-primary">{copy.forecast.title}</h1>

      <Card tint>
        <h2 className="mb-3 text-lg font-bold text-ink-primary">{copy.forecast.formTitle}</h2>
        <form className="space-y-4" onSubmit={handleSubmit} noValidate>
          <div>
            <label className="mb-1 block text-base font-medium text-ink-secondary" htmlFor="crop">
              {copy.forecast.cropLabel}
            </label>
            <Select
              id="crop"
              className="min-h-[44px]"
              value={form.cropType}
              onChange={(v) => setForm((f) => ({ ...f, cropType: v as CropType }))}
              options={cropOptions}
            />
          </div>

          <div>
            <label className="mb-1 block text-base font-medium text-ink-secondary" htmlFor="area">
              {copy.forecast.areaLabel}
            </label>
            <input
              id="area"
              type="number"
              min={0.1}
              step={0.1}
              placeholder={copy.forecast.areaPlaceholder}
              className={`min-h-[44px] w-full rounded-lg border bg-white px-3 text-base text-ink-primary transition-colors focus:outline-none focus:ring-2 ${
                touched && errors.areaHa
                  ? 'border-status-critical focus:ring-status-critical/30'
                  : 'border-line-axis focus:border-brand-500 focus:ring-brand-500/30'
              }`}
              value={form.areaHa}
              onChange={(e) => setForm((f) => ({ ...f, areaHa: Number(e.target.value) }))}
              aria-invalid={touched && !!errors.areaHa}
            />
            {touched && errors.areaHa && <p className="mt-1 text-sm text-status-critical">{errors.areaHa}</p>}
          </div>

          <div>
            <label className="mb-1 block text-base font-medium text-ink-secondary" htmlFor="planting-date">
              {copy.forecast.plantingDateLabel}
            </label>
            <input
              id="planting-date"
              type="date"
              className={`min-h-[44px] w-full rounded-lg border bg-white px-3 text-base text-ink-primary transition-colors focus:outline-none focus:ring-2 ${
                touched && errors.plantingDate
                  ? 'border-status-critical focus:ring-status-critical/30'
                  : 'border-line-axis focus:border-brand-500 focus:ring-brand-500/30'
              }`}
              value={form.plantingDate}
              onChange={(e) => setForm((f) => ({ ...f, plantingDate: e.target.value }))}
              aria-invalid={touched && !!errors.plantingDate}
            />
            {touched && errors.plantingDate && <p className="mt-1 text-sm text-status-critical">{errors.plantingDate}</p>}
          </div>

          <div>
            <label className="mb-1 block text-base font-medium text-ink-secondary" htmlFor="district">
              {copy.forecast.districtLabel}
            </label>
            <Select
              id="district"
              className="min-h-[44px]"
              value={form.district}
              onChange={(v) => setForm((f) => ({ ...f, district: v }))}
              options={districts.map((d) => ({ value: d, label: d }))}
            />
          </div>

          <Button type="submit" fullWidth disabled={status === 'loading'}>
            {status === 'loading' ? copy.forecast.predicting : copy.forecast.submitButton}
          </Button>
        </form>
      </Card>

      {status === 'loading' && <Spinner label={copy.forecast.predicting} />}

      {status === 'error' && (
        <div className="mt-4">
          <EmptyState
            tone={offline ? 'offline' : 'error'}
            title={offline ? copy.common.backendUnreachableTitle : copy.forecast.errorTitle}
            description={offline ? copy.common.backendUnreachableDesc : undefined}
            onRetry={() => void runPrediction()}
            retryLabel={copy.common.retry}
          />
        </div>
      )}

      {status === 'success' && result && (
        <div className="mt-4 space-y-4">
          <Card tint className="border-brand-200">
            <h2 className="mb-1 text-base font-medium text-ink-secondary">{copy.forecast.predictedYieldLabel}</h2>
            <p className="text-4xl font-extrabold text-brand-700">
              {result.predictedYieldTPerHa} <span className="text-xl font-semibold text-ink-secondary">tấn/ha</span>
            </p>
            <p className="mt-1 text-base text-ink-secondary">
              {copy.forecast.totalOutputLabel}: <span className="font-bold text-ink-primary">{result.totalOutputTons} tấn</span>
            </p>
          </Card>

          <Card tint>
            <h3 className="mb-1 text-base font-medium text-ink-secondary">{copy.forecast.harvestWindowLabel}</h3>
            <p className="text-xl font-bold text-ink-primary">
              {formatDateVi(result.harvestWindowStart)} — {formatDateVi(result.harvestWindowEnd)}
            </p>
          </Card>

          <Card tint>
            <div className="flex flex-wrap items-center gap-3">
              <Badge tone={riskTone[result.risk]} label={`${copy.forecast.riskLabel}: ${copy.forecast.risk[result.risk]}`} />
              <span className="text-base text-ink-secondary">
                {copy.forecast.confidenceLabel}: <span className="font-bold text-ink-primary">{Math.round(result.confidence * 100)}%</span>
              </span>
            </div>
            <p className="mt-2 text-base text-ink-secondary">{result.riskNote}</p>
          </Card>

          <Card tint>
            <h3 className="mb-2 text-lg font-bold text-ink-primary">{copy.forecast.rationaleTitle}</h3>
            <ul className="list-disc space-y-1.5 pl-5">
              {result.rationale.map((r, i) => (
                <li key={i} className="text-base text-ink-primary">
                  {r}
                </li>
              ))}
            </ul>
          </Card>
        </div>
      )}
    </div>
  );
}
