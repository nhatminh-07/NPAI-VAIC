'use client';

import { useRef, useState } from 'react';
import type { ChangeEvent, DragEvent } from 'react';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Select } from '@/components/ui/Select';
import { Badge } from '@/components/ui/Badge';
import type { BadgeTone } from '@/components/ui/Badge';
import { Spinner } from '@/components/ui/Spinner';
import { ConfidenceBar } from '@/components/ui/ConfidenceBar';
import { EmptyState } from '@/components/ui/EmptyState';
import { copy } from '@/constants/copy';
import { ApiError, detectDisease } from '@/lib/api';
import type { CropType, DiseaseDetectionResult, Severity } from '@/types/api';

// idle = chưa phân tích, loading = đang gọi API, success = có kết quả, error = gọi lỗi.
type Status = 'idle' | 'loading' | 'success' | 'error';

// Ánh xạ mức độ bệnh (trả về từ backend) sang màu Badge tương ứng.
const severityTone: Record<Severity, BadgeTone> = {
  healthy: 'good',
  mild: 'warning',
  moderate: 'serious',
  severe: 'critical',
};

// Danh sách loại cây trồng cho dropdown "Loại cây trồng" - dùng chung format với
// forecast/page.tsx (copy.forecast.crop.*) để tránh lặp chuỗi dịch.
const cropOptions: { value: CropType; label: string }[] = [
  { value: 'rice', label: copy.forecast.crop.rice },
  { value: 'coffee', label: copy.forecast.crop.coffee },
  { value: 'vegetable', label: copy.forecast.crop.vegetable },
];

// Trang chẩn đoán bệnh cây (nông dân chụp/tải ảnh lá cây lên, kèm loại cây trồng và
// số cây bị ảnh hưởng, để backend chẩn đoán bệnh + gợi ý cách xử lý).
export default function ScanPage() {
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [status, setStatus] = useState<Status>('idle');
  const [result, setResult] = useState<DiseaseDetectionResult | null>(null);
  const [checked, setChecked] = useState<Record<number, boolean>>({});
  const [isDragOver, setIsDragOver] = useState(false);
  const [offline, setOffline] = useState(false);
  const [cropType, setCropType] = useState<CropType>('rice');
  const [affectedPlantCount, setAffectedPlantCount] = useState('');
  const [touched, setTouched] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  // Hợp lệ khi đã nhập và > 0. Lưu ý: chỉ HIỂN THỊ lỗi này khi `touched` = true (sau
  // khi người dùng đã bấm "Phân tích" ít nhất 1 lần), để không báo lỗi ngay khi vừa
  // chọn ảnh xong mà chưa kịp nhập gì.
  const affectedPlantCountError =
    affectedPlantCount !== '' && Number(affectedPlantCount) > 0 ? undefined : copy.scan.affectedPlantCountError;

  // Dùng chung cho cả 2 luồng chọn ảnh: kéo-thả (handleDrop) và bấm chọn file
  // (handleFileChange). Reset kết quả/trạng thái cũ vì đây coi như 1 lượt chẩn đoán mới.
  function selectFile(selected: File) {
    setFile(selected);
    setPreviewUrl(URL.createObjectURL(selected));
    setResult(null);
    setStatus('idle');
    setChecked({});
  }

  function handleFileChange(e: ChangeEvent<HTMLInputElement>) {
    const selected = e.target.files?.[0];
    if (selected) selectFile(selected);
  }

  function handleDrop(e: DragEvent<HTMLLabelElement>) {
    e.preventDefault();
    setIsDragOver(false);
    const dropped = e.dataTransfer.files?.[0];
    if (dropped) selectFile(dropped);
  }

  async function handleAnalyze() {
    if (!file) return;
    setTouched(true); // bật hiển thị lỗi validate (nếu có) từ giờ trở đi
    if (affectedPlantCountError) return;
    setStatus('loading');
    try {
      const res = await detectDisease(file, cropType, Number(affectedPlantCount));
      setResult(res);
      setStatus('success');
    } catch (err) {
      setOffline(err instanceof ApiError && err.offline);
      setStatus('error');
    }
  }

  // Dùng lại cho cả 3 nút "Lưu báo cáo" / "Chụp lại" / "Bỏ qua": báo cáo đã được
  // backend lưu lại NGAY khi gọi detectDisease() thành công (không cần gọi API lần 2
  // để "lưu"), nên cả 3 nút chỉ cần đưa người dùng quay về màn chọn ảnh ban đầu.
  function handleRetake() {
    setFile(null);
    setPreviewUrl(null);
    setResult(null);
    setStatus('idle');
    setChecked({});
    setCropType('rice');
    setAffectedPlantCount('');
    setTouched(false);
    if (inputRef.current) inputRef.current.value = '';
  }

  return (
    <div className="mx-auto max-w-md px-4 py-5">
      <h1 className="mb-4 text-2xl font-bold text-ink-primary">{copy.scan.title}</h1>

      {!previewUrl && (
        <label
          htmlFor="scan-upload"
          onDragOver={(e) => {
            e.preventDefault();
            setIsDragOver(true);
          }}
          onDragLeave={() => setIsDragOver(false)}
          onDrop={handleDrop}
          className={`flex min-h-[220px] cursor-pointer flex-col items-center justify-center gap-3 rounded-2xl border-2 border-dashed px-4 text-center transition-colors ${
            isDragOver ? 'border-brand-500 bg-brand-50' : 'border-line-axis bg-surface hover:border-brand-300 hover:bg-brand-50/40'
          }`}
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5} className="h-14 w-14 text-ink-muted">
            <path strokeLinecap="round" strokeLinejoin="round" d="M4 8V6a2 2 0 012-2h2M20 8V6a2 2 0 00-2-2h-2M4 16v2a2 2 0 002 2h2m10-4v2a2 2 0 01-2 2h-2" />
            <circle cx="12" cy="12" r="3.5" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
          <p className="text-lg font-semibold text-ink-primary">{copy.scan.uploadPrompt}</p>
          <p className="text-base text-ink-secondary">{copy.scan.uploadHint}</p>
          <input
            ref={inputRef}
            id="scan-upload"
            type="file"
            accept="image/*"
            capture="environment"
            className="hidden"
            onChange={handleFileChange}
          />
        </label>
      )}

      {previewUrl && (
        <div className="space-y-4">
          <Card className="p-2">
            <div className="relative overflow-hidden rounded-xl">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={previewUrl} alt="Ảnh cây trồng đã chọn" className="max-h-80 w-full object-cover" />
              {status === 'success' && (
                // Placeholder cho tính năng bản đồ nhiệt (khoanh vùng bị bệnh trên ảnh) -
                // backend/model chưa hỗ trợ, chỉ hiện dòng chữ báo "sẽ có ở bản sau".
                <span className="absolute bottom-2 left-2 rounded-md bg-black/60 px-2 py-1 text-xs text-white">
                  {copy.scan.heatmapPlaceholder}
                </span>
              )}
            </div>
          </Card>

          {status !== 'success' && (
            <>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="mb-1 block text-base font-medium text-ink-secondary" htmlFor="crop-type">
                    {copy.forecast.cropLabel}
                  </label>
                  <Select
                    id="crop-type"
                    className="min-h-[44px]"
                    value={cropType}
                    onChange={(v) => setCropType(v as CropType)}
                    options={cropOptions}
                  />
                </div>

                <div>
                  <label className="mb-1 block text-base font-medium text-ink-secondary" htmlFor="affected-plant-count">
                    {copy.scan.affectedPlantCountLabel}
                  </label>
                  <input
                    id="affected-plant-count"
                    type="number"
                    min={1}
                    step={1}
                    inputMode="numeric"
                    placeholder={copy.scan.affectedPlantCountPlaceholder}
                    className={`min-h-[44px] w-full rounded-lg border bg-white px-3 text-base text-ink-primary transition-colors focus:outline-none focus:ring-2 ${
                      touched && affectedPlantCountError
                        ? 'border-status-critical focus:ring-status-critical/30'
                        : 'border-line-axis focus:border-brand-500 focus:ring-brand-500/30'
                    }`}
                    value={affectedPlantCount}
                    onChange={(e) => setAffectedPlantCount(e.target.value)}
                    aria-invalid={touched && !!affectedPlantCountError}
                  />
                  {touched && affectedPlantCountError && (
                    <p className="mt-1 text-sm text-status-critical">{affectedPlantCountError}</p>
                  )}
                </div>
              </div>

              <div className="flex gap-3">
                <Button variant="secondary" fullWidth onClick={() => inputRef.current?.click()}>
                  {copy.scan.changePhoto}
                </Button>
                <Button fullWidth onClick={handleAnalyze} disabled={status === 'loading'}>
                  {status === 'loading' ? copy.scan.analyzing : copy.scan.analyzeButton}
                </Button>
                <input
                  ref={inputRef}
                  type="file"
                  accept="image/*"
                  capture="environment"
                  className="hidden"
                  onChange={handleFileChange}
                />
              </div>
            </>
          )}

          {status === 'loading' && <Spinner label={copy.scan.analyzing} />}

          {status === 'error' && (
            <EmptyState
              tone={offline ? 'offline' : 'error'}
              title={offline ? copy.common.backendUnreachableTitle : copy.scan.errorTitle}
              description={offline ? copy.common.backendUnreachableDesc : undefined}
              onRetry={handleAnalyze}
              retryLabel={copy.common.retry}
            />
          )}

          {status === 'success' && result && (
            <div className="space-y-4">
              <Card tint>
                <h2 className="text-2xl font-bold text-ink-primary">{result.diseaseName}</h2>
                <p className="mb-3 text-base italic text-ink-secondary">{result.scientificName}</p>
                <div className="mb-3">
                  <Badge tone={severityTone[result.severity]} label={`${copy.scan.severityLabel}: ${copy.scan.severity[result.severity]}`} />
                </div>
                <ConfidenceBar confidence={result.confidence} label={copy.scan.confidenceLabel} />
              </Card>

              {result.confidence < 0.6 && (
                <Card className="border-status-warning/50 bg-status-warning/10">
                  <div className="flex gap-2">
                    <svg viewBox="0 0 20 20" fill="currentColor" className="h-6 w-6 shrink-0 text-[#8a5a00]">
                      <path fillRule="evenodd" d="M8.3 3.3a2 2 0 013.4 0l6.4 11.1A2 2 0 0116.4 17H3.6a2 2 0 01-1.7-2.6L8.3 3.3zM10 7a1 1 0 011 1v3a1 1 0 11-2 0V8a1 1 0 011-1zm0 7a1 1 0 100 2 1 1 0 000-2z" clipRule="evenodd" />
                    </svg>
                    <p className="text-base font-medium text-[#8a5a00]">{copy.scan.lowConfidenceWarning}</p>
                  </div>
                </Card>
              )}

              <Card tint>
                <h3 className="mb-3 text-lg font-bold text-ink-primary">{copy.scan.recommendationsTitle}</h3>
                <ul className="space-y-2">
                  {result.recommendations.map((rec, i) => (
                    <li key={i}>
                      <label className="flex min-h-[44px] cursor-pointer items-start gap-3 rounded-lg px-2 py-2 hover:bg-plane">
                        <input
                          type="checkbox"
                          checked={!!checked[i]}
                          onChange={() => setChecked((c) => ({ ...c, [i]: !c[i] }))}
                          className="mt-1 h-5 w-5 shrink-0 accent-brand-600"
                        />
                        <span
                          className={`text-base ${checked[i] ? 'text-ink-muted line-through' : 'text-ink-primary'}`}
                        >
                          {rec}
                        </span>
                      </label>
                    </li>
                  ))}
                </ul>
              </Card>

              <Button fullWidth onClick={handleRetake}>
                {copy.scan.saveReport}
              </Button>
              <div className="flex gap-3">
                <Button variant="secondary" fullWidth onClick={handleRetake}>
                  {copy.scan.retake}
                </Button>
                <Button variant="secondary" fullWidth onClick={handleRetake}>
                  {copy.scan.skip}
                </Button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
