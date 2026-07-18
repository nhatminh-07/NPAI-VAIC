'use client';

// Trang "Quản lý" của cán bộ nông nghiệp: tạo các VÙNG CANH TÁC (khu vực canh tác
// thuộc 1 huyện của Điện Biên, có diện tích cụ thể). Nông dân sẽ chọn 1 trong các
// vùng này khi khai báo vụ canh tác của mình ở trang /management (farmer).
// Xem chi tiết API contract (backend CHƯA implement) tại lib/api.ts.

import { useEffect, useState } from 'react';
import type { FormEvent } from 'react';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Select } from '@/components/ui/Select';
import { EmptyState } from '@/components/ui/EmptyState';
import { Skeleton } from '@/components/ui/Skeleton';
import { copy } from '@/constants/copy';
import { districts } from '@/constants/districts';
import { ApiError, createFarmingRegion, getFarmingRegions } from '@/lib/api';
import type { FarmingRegion } from '@/types/api';

type ListStatus = 'idle' | 'loading' | 'success' | 'error';
type SubmitStatus = 'idle' | 'submitting' | 'error';

function formatDateVi(iso: string): string {
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? iso : d.toLocaleDateString('vi-VN');
}

export default function RegionManagementPage() {
  const [name, setName] = useState('');
  const [district, setDistrict] = useState(districts[0]);
  const [areaHa, setAreaHa] = useState('');
  const [touched, setTouched] = useState(false);
  const [submitStatus, setSubmitStatus] = useState<SubmitStatus>('idle');
  const [submitOffline, setSubmitOffline] = useState(false);

  const [listStatus, setListStatus] = useState<ListStatus>('idle');
  const [regions, setRegions] = useState<FarmingRegion[]>([]);
  const [listOffline, setListOffline] = useState(false);
  const [retryToken, setRetryToken] = useState(0);

  const nameError = name.trim() === '' ? copy.regionManagement.nameError : undefined;
  const areaError = areaHa !== '' && Number(areaHa) > 0 ? undefined : copy.forecast.areaError;

  // Tải danh sách vùng canh tác đã có; gọi lại mỗi khi tạo mới thành công (retryToken)
  // hoặc bấm "Thử lại" sau khi lỗi.
  useEffect(() => {
    let cancelled = false;
    setListStatus('loading');
    getFarmingRegions()
      .then((res) => {
        if (cancelled) return;
        setRegions(res.regions);
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
    if (nameError || areaError) return;

    setSubmitStatus('submitting');
    try {
      await createFarmingRegion({ name: name.trim(), district, areaHa: Number(areaHa) });
      setName('');
      setAreaHa('');
      setTouched(false);
      setSubmitStatus('idle');
      setRetryToken((t) => t + 1); // tải lại danh sách để hiện vùng vừa tạo
    } catch (err) {
      setSubmitOffline(err instanceof ApiError && err.offline);
      setSubmitStatus('error');
    }
  }

  return (
    <div className="mx-auto max-w-4xl">
      <h1 className="mb-6 text-2xl font-bold text-ink-primary">{copy.regionManagement.title}</h1>

      <Card tint className="mb-6">
        <h2 className="mb-3 text-lg font-bold text-ink-primary">{copy.regionManagement.createTitle}</h2>
        <form className="space-y-4" onSubmit={handleSubmit} noValidate>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <div className="sm:col-span-2">
              <label className="mb-1 block text-base font-medium text-ink-secondary" htmlFor="region-name">
                {copy.regionManagement.nameLabel}
              </label>
              <input
                id="region-name"
                type="text"
                placeholder={copy.regionManagement.namePlaceholder}
                className={`min-h-[44px] w-full rounded-lg border bg-white px-3 text-base text-ink-primary transition-colors focus:outline-none focus:ring-2 ${
                  touched && nameError
                    ? 'border-status-critical focus:ring-status-critical/30'
                    : 'border-line-axis focus:border-brand-500 focus:ring-brand-500/30'
                }`}
                value={name}
                onChange={(e) => setName(e.target.value)}
                aria-invalid={touched && !!nameError}
              />
              {touched && nameError && <p className="mt-1 text-sm text-status-critical">{nameError}</p>}
            </div>

            <div>
              <label className="mb-1 block text-base font-medium text-ink-secondary" htmlFor="region-area">
                {copy.forecast.areaLabel}
              </label>
              <input
                id="region-area"
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
          </div>

          <div className="max-w-xs">
            <label className="mb-1 block text-base font-medium text-ink-secondary" htmlFor="region-district">
              {copy.forecast.districtLabel}
            </label>
            <Select
              id="region-district"
              className="min-h-[44px]"
              value={district}
              onChange={setDistrict}
              options={districts.map((d) => ({ value: d, label: d }))}
            />
          </div>

          {submitStatus === 'error' && (
            <p className="text-sm text-status-critical">
              {submitOffline ? copy.common.backendUnreachableDesc : copy.regionManagement.createErrorTitle}
            </p>
          )}

          <Button type="submit" disabled={submitStatus === 'submitting'}>
            {submitStatus === 'submitting' ? copy.regionManagement.creating : copy.regionManagement.submitButton}
          </Button>
        </form>
      </Card>

      <h2 className="mb-3 text-lg font-bold text-ink-primary">{copy.regionManagement.listTitle}</h2>

      {listStatus === 'loading' && (
        <Card tint>
          <Skeleton className="h-32 w-full" />
        </Card>
      )}

      {listStatus === 'error' && (
        <EmptyState
          tone={listOffline ? 'offline' : 'error'}
          title={listOffline ? copy.common.backendUnreachableTitle : copy.regionManagement.loadErrorTitle}
          description={listOffline ? copy.common.backendUnreachableDesc : undefined}
          onRetry={() => setRetryToken((t) => t + 1)}
          retryLabel={copy.common.retry}
        />
      )}

      {listStatus === 'success' &&
        (regions.length === 0 ? (
          <EmptyState tone="offline" title={copy.common.empty} />
        ) : (
          <Card tint>
            <div className="overflow-x-auto">
              <table className="w-full min-w-[480px] border-collapse text-left">
                <thead>
                  <tr className="border-b border-line-border">
                    <th className="px-3 py-2 text-sm font-semibold text-ink-secondary">{copy.regionManagement.columns.name}</th>
                    <th className="px-3 py-2 text-sm font-semibold text-ink-secondary">{copy.regionManagement.columns.district}</th>
                    <th className="px-3 py-2 text-sm font-semibold text-ink-secondary">{copy.regionManagement.columns.area}</th>
                    <th className="px-3 py-2 text-sm font-semibold text-ink-secondary">{copy.regionManagement.columns.createdAt}</th>
                  </tr>
                </thead>
                <tbody>
                  {regions.map((r) => (
                    <tr key={r.id} className="border-b border-line-grid last:border-0">
                      <td className="px-3 py-2 text-base font-medium text-ink-primary">{r.name}</td>
                      <td className="px-3 py-2 text-base text-ink-primary">{r.district}</td>
                      <td className="px-3 py-2 text-base tabular-nums text-ink-primary">{r.areaHa}</td>
                      <td className="px-3 py-2 text-base text-ink-secondary">{formatDateVi(r.createdAt)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        ))}
    </div>
  );
}
