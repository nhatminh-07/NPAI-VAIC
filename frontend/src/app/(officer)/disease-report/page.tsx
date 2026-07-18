'use client';

import { useEffect, useState } from 'react';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import type { BadgeTone } from '@/components/ui/Badge';
import { Skeleton } from '@/components/ui/Skeleton';
import { EmptyState } from '@/components/ui/EmptyState';
import { copy } from '@/constants/copy';
import { ApiError, getDiseaseReport } from '@/lib/api';
import type { DiseaseReportEntry, Severity } from '@/types/api';

type Status = 'idle' | 'loading' | 'success' | 'error';

const severityTone: Record<Severity, BadgeTone> = {
  healthy: 'good',
  mild: 'warning',
  moderate: 'serious',
  severe: 'critical',
};

const cropLabel: Record<DiseaseReportEntry['cropType'], string> = {
  rice: copy.forecast.crop.rice,
  coffee: copy.forecast.crop.coffee,
  vegetable: copy.forecast.crop.vegetable,
};

function formatDateVi(iso: string): string {
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? iso : d.toLocaleDateString('vi-VN');
}

function ReportSkeleton() {
  return (
    <Card tint>
      <Skeleton className="mb-3 h-5 w-48" />
      <Skeleton className="h-64 w-full" />
    </Card>
  );
}

export default function DiseaseReportPage() {
  const [status, setStatus] = useState<Status>('idle');
  const [reports, setReports] = useState<DiseaseReportEntry[]>([]);
  const [retryToken, setRetryToken] = useState(0);
  const [offline, setOffline] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setStatus('loading');
    getDiseaseReport()
      .then((res) => {
        if (cancelled) return;
        setReports(res.reports);
        setStatus('success');
      })
      .catch((err) => {
        if (cancelled) return;
        setOffline(err instanceof ApiError && err.offline);
        setStatus('error');
      });
    return () => {
      cancelled = true;
    };
  }, [retryToken]);

  return (
    <div className="mx-auto max-w-6xl">
      <h1 className="mb-6 text-2xl font-bold text-ink-primary">{copy.diseaseReport.title}</h1>

      {status === 'loading' && <ReportSkeleton />}

      {status === 'error' && (
        <EmptyState
          tone={offline ? 'offline' : 'error'}
          title={offline ? copy.common.backendUnreachableTitle : copy.diseaseReport.errorTitle}
          description={offline ? copy.common.backendUnreachableDesc : undefined}
          onRetry={() => setRetryToken((t) => t + 1)}
          retryLabel={copy.common.retry}
        />
      )}

      {status === 'success' &&
        (reports.length === 0 ? (
          <EmptyState tone="offline" title={copy.common.empty} />
        ) : (
          <Card tint>
            <div className="overflow-x-auto">
              <table className="w-full min-w-[600px] border-collapse text-left">
                <thead>
                  <tr className="border-b border-line-border">
                    <th className="px-3 py-2 text-sm font-semibold text-ink-secondary">{copy.diseaseReport.columns.district}</th>
                    <th className="px-3 py-2 text-sm font-semibold text-ink-secondary">{copy.diseaseReport.columns.crop}</th>
                    <th className="px-3 py-2 text-sm font-semibold text-ink-secondary">{copy.diseaseReport.columns.diseaseName}</th>
                    <th className="px-3 py-2 text-sm font-semibold text-ink-secondary">{copy.diseaseReport.columns.severity}</th>
                    <th className="px-3 py-2 text-sm font-semibold text-ink-secondary">{copy.diseaseReport.columns.affectedPlantCount}</th>
                    <th className="px-3 py-2 text-sm font-semibold text-ink-secondary">{copy.diseaseReport.columns.reportedAt}</th>
                  </tr>
                </thead>
                <tbody>
                  {reports.map((r) => (
                    <tr key={r.id} className="border-b border-line-grid last:border-0">
                      <td className="px-3 py-2 text-base font-medium text-ink-primary">{r.district}</td>
                      <td className="px-3 py-2 text-base text-ink-primary">{cropLabel[r.cropType]}</td>
                      <td className="px-3 py-2 text-base text-ink-primary">{r.diseaseName}</td>
                      <td className="px-3 py-2">
                        <Badge tone={severityTone[r.severity]} label={copy.scan.severity[r.severity]} />
                      </td>
                      <td className="px-3 py-2 text-base tabular-nums text-ink-primary">{r.affectedPlantCount}</td>
                      <td className="px-3 py-2 text-base text-ink-secondary">{formatDateVi(r.reportedAt)}</td>
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
