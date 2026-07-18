'use client';

// Trang "Quản lý" của nông dân (route: /farming-periods): khai báo VỤ CANH TÁC (diện
// tích, loại cây trồng, số lượng cây) trong 1 VÙNG CANH TÁC do cán bộ nông nghiệp đã
// tạo sẵn (trang /management bên phía cán bộ). Xem chi tiết API contract (backend
// CHƯA implement) tại lib/api.ts.

import { useEffect, useState } from 'react';
import type { FormEvent } from 'react';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Select } from '@/components/ui/Select';
import { EmptyState } from '@/components/ui/EmptyState';
import { Skeleton } from '@/components/ui/Skeleton';
import { copy } from '@/constants/copy';
import { ApiError, createFarmingPeriod, getFarmingPeriods, getFarmingRegions } from '@/lib/api';
import type { CropType, FarmingPeriod, FarmingRegion } from '@/types/api';

type LoadStatus = 'idle' | 'loading' | 'success' | 'error';
type SubmitStatus = 'idle' | 'submitting' | 'error';

const cropOptions: { value: CropType; label: string }[] = [
  { value: 'rice', label: copy.forecast.crop.rice },
  { value: 'coffee', label: copy.forecast.crop.coffee },
  { value: 'vegetable', label: copy.forecast.crop.vegetable },
];

function formatDateVi(iso: string): string {
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? iso : d.toLocaleDateString('vi-VN');
}

export default function PeriodManagementPage() {
  // Danh sách vùng canh tác do cán bộ tạo, dùng để đổ vào dropdown chọn vùng bên dưới.
  const [regionStatus, setRegionStatus] = useState<LoadStatus>('idle');
  const [regions, setRegions] = useState<FarmingRegion[]>([]);

  const [regionId, setRegionId] = useState('');
  const [cropType, setCropType] = useState<CropType>('rice');
  const [areaHa, setAreaHa] = useState('');
  const [cropCount, setCropCount] = useState('');
  const [touched, setTouched] = useState(false);
  const [submitStatus, setSubmitStatus] = useState<SubmitStatus>('idle');
  const [submitOffline, setSubmitOffline] = useState(false);

  const [listStatus, setListStatus] = useState<LoadStatus>('idle');
  const [periods, setPeriods] = useState<FarmingPeriod[]>([]);
  const [listOffline, setListOffline] = useState(false);
  const [retryToken, setRetryToken] = useState(0);

  const areaError = areaHa !== '' && Number(areaHa) > 0 ? undefined : copy.forecast.areaError;
  const cropCountError = cropCount !== '' && Number(cropCount) > 0 ? undefined : copy.periodManagement.cropCountError;

  useEffect(() => {
    let cancelled = false;
    setRegionStatus('loading');
    getFarmingRegions()
      .then((res) => {
        if (cancelled) return;
        setRegions(res.regions);
        if (res.regions.length > 0) setRegionId(String(res.regions[0].id));
        setRegionStatus('success');
      })
      .catch(() => {
        if (cancelled) return;
        setRegionStatus('error');
      });
    return () => {
      cancelled = true;
    };
  }, []);

  // Tải danh sách vụ canh tác đã khai báo; gọi lại sau khi tạo mới thành công hoặc bấm "Thử lại".
  useEffect(() => {
    let cancelled = false;
    setListStatus('loading');
    getFarmingPeriods()
      .then((res) => {
        if (cancelled) return;
        setPeriods(res.periods);
        setListStatus('success');
      })
      .catch((err) => {
        if (cancelled) return;
        setListOffline(err instanceof ApiError && err.offline);
        setListStatus('error');
      });
    return () => {
      cancelled = true;
    };
  }, [retryToken]);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setTouched(true);
    if (!regionId || areaError || cropCountError) return;

    setSubmitStatus('submitting');
    try {
      await createFarmingPeriod({
        regionId: Number(regionId),
        cropType,
        areaHa: Number(areaHa),
        cropCount: Number(cropCount),
      });
      setAreaHa('');
      setCropCount('');
      setTouched(false);
      setSubmitStatus('idle');
      setRetryToken((t) => t + 1); // tải lại danh sách để hiện vụ vừa thêm
    } catch (err) {
      setSubmitOffline(err instanceof ApiError && err.offline);
      setSubmitStatus('error');
    }
  }

  const hasRegions = regions.length > 0;

  return (
    <div className="mx-auto max-w-md px-4 py-5">
      <h1 className="mb-4 text-2xl font-bold text-ink-primary">{copy.periodManagement.title}</h1>

      <Card tint>
        <h2 className="mb-3 text-lg font-bold text-ink-primary">{copy.periodManagement.createTitle}</h2>

        {/* Hiện gợi ý khi KHÔNG có vùng nào để chọn - dù là do danh sách rỗng
            (regionStatus 'success' nhưng mảng rỗng) hay do gọi API bị lỗi (regionStatus
            'error') - cả 2 trường hợp đều khiến nút submit bị vô hiệu hoá bên dưới, nên
            đều cần giải thích cho nông dân biết vì sao. */}
        {(regionStatus === 'error' || (regionStatus === 'success' && !hasRegions)) && (
          <p className="mb-4 rounded-lg border border-status-warning/40 bg-status-warning/10 p-3 text-sm text-[#8a5a00]">
            {copy.periodManagement.noRegionsHint}
          </p>
        )}

        <form className="space-y-4" onSubmit={handleSubmit} noValidate>
          <div>
            <label className="mb-1 block text-base font-medium text-ink-secondary" htmlFor="period-region">
              {copy.periodManagement.regionLabel}
            </label>
            <Select
              id="period-region"
              className="min-h-[44px]"
              value={regionId}
              onChange={setRegionId}
              options={regions.map((r) => ({ value: String(r.id), label: `${r.name} (${r.district})` }))}
            />
          </div>

          <div>
            <label className="mb-1 block text-base font-medium text-ink-secondary" htmlFor="period-crop">
              {copy.forecast.cropLabel}
            </label>
            <Select
              id="period-crop"
              className="min-h-[44px]"
              value={cropType}
              onChange={(v) => setCropType(v as CropType)}
              options={cropOptions}
            />
          </div>

          <div>
            <label className="mb-1 block text-base font-medium text-ink-secondary" htmlFor="period-area">
              {copy.forecast.areaLabel}
            </label>
            <input
              id="period-area"
              type="number"
              min={0.1}
              step={0.1}
              placeholder={copy.forecast.areaPlaceholder}
              className={`min-h-[44px] w-full rounded-lg border bg-white px-3 text-base text-ink-primary transition-colors focus:outline-none focus:ring-2 ${
                touched && areaError
                  ? 'border-status-critical focus:ring-status-critical/30'
                  : 'border-line-axis focus:border-brand-500 focus:ring-brand-500/30'
              }`}
              value={areaHa}
              onChange={(e) => setAreaHa(e.target.value)}
              aria-invalid={touched && !!areaError}
            />
            {touched && areaError && <p className="mt-1 text-sm text-status-critical">{areaError}</p>}
          </div>

          <div>
            <label className="mb-1 block text-base font-medium text-ink-secondary" htmlFor="period-crop-count">
              {copy.periodManagement.cropCountLabel}
            </label>
            <input
              id="period-crop-count"
              type="number"
              min={1}
              step={1}
              inputMode="numeric"
              placeholder={copy.periodManagement.cropCountPlaceholder}
              className={`min-h-[44px] w-full rounded-lg border bg-white px-3 text-base text-ink-primary transition-colors focus:outline-none focus:ring-2 ${
                touched && cropCountError
                  ? 'border-status-critical focus:ring-status-critical/30'
                  : 'border-line-axis focus:border-brand-500 focus:ring-brand-500/30'
              }`}
              value={cropCount}
              onChange={(e) => setCropCount(e.target.value)}
              aria-invalid={touched && !!cropCountError}
            />
            {touched && cropCountError && <p className="mt-1 text-sm text-status-critical">{cropCountError}</p>}
          </div>

          {submitStatus === 'error' && (
            <p className="text-sm text-status-critical">
              {submitOffline ? copy.common.backendUnreachableDesc : copy.periodManagement.createErrorTitle}
            </p>
          )}

          <Button type="submit" fullWidth disabled={submitStatus === 'submitting' || !hasRegions}>
            {submitStatus === 'submitting' ? copy.periodManagement.creating : copy.periodManagement.submitButton}
          </Button>
        </form>
      </Card>

      <h2 className="mb-3 mt-6 text-lg font-bold text-ink-primary">{copy.periodManagement.listTitle}</h2>

      {listStatus === 'loading' && (
        <Card tint>
          <Skeleton className="h-24 w-full" />
        </Card>
      )}

      {listStatus === 'error' && (
        <EmptyState
          tone={listOffline ? 'offline' : 'error'}
          title={listOffline ? copy.common.backendUnreachableTitle : copy.periodManagement.loadErrorTitle}
          description={listOffline ? copy.common.backendUnreachableDesc : undefined}
          onRetry={() => setRetryToken((t) => t + 1)}
          retryLabel={copy.common.retry}
        />
      )}

      {listStatus === 'success' &&
        (periods.length === 0 ? (
          <EmptyState tone="offline" title={copy.common.empty} />
        ) : (
          <div className="space-y-3">
            {periods.map((p) => (
              <Card key={p.id} tint>
                <div className="flex items-center justify-between">
                  <span className="font-bold text-ink-primary">{p.regionName}</span>
                  <span className="text-sm text-ink-secondary">{formatDateVi(p.createdAt)}</span>
                </div>
                <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-sm text-ink-secondary">
                  <span>
                    {copy.periodManagement.columns.crop}: <span className="font-medium text-ink-primary">{cropOptions.find((c) => c.value === p.cropType)?.label ?? p.cropType}</span>
                  </span>
                  <span>
                    {copy.periodManagement.columns.area}: <span className="font-medium text-ink-primary">{p.areaHa}</span>
                  </span>
                  <span>
                    {copy.periodManagement.columns.cropCount}: <span className="font-medium text-ink-primary">{p.cropCount}</span>
                  </span>
                </div>
              </Card>
            ))}
          </div>
        ))}
    </div>
  );
}
