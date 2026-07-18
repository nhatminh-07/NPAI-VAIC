'use client';

import { useEffect, useMemo, useState } from 'react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { Card } from '@/components/ui/Card';
import { Select } from '@/components/ui/Select';
import { Skeleton } from '@/components/ui/Skeleton';
import { EmptyState } from '@/components/ui/EmptyState';
import { copy } from '@/constants/copy';
import { ApiError, getDashboard } from '@/lib/api';
import { crops } from '@/constants/crops';
import { recentQuarterOptions } from '@/constants/periods';
import type { DashboardResult, DistrictRanking } from '@/types/api';

type Status = 'idle' | 'loading' | 'success' | 'error';
type SortKey = keyof Pick<DistrictRanking, 'district' | 'yieldTPerHa' | 'outputTons' | 'diseaseCases'>;

const seriesPalette = ['#16a34a', '#0d9488', '#84a98c', '#d97706', '#65a30d'];
const quarterOptions = recentQuarterOptions();

function DeltaLabel({ value, suffix }: { value: number; suffix: string }) {
  const isUp = value >= 0;
  return (
    <span className={`inline-flex items-center gap-1 text-sm font-semibold ${isUp ? 'text-[#006300]' : 'text-status-critical'}`}>
      <svg viewBox="0 0 20 20" fill="currentColor" className={`h-3.5 w-3.5 ${isUp ? '' : 'rotate-180'}`}>
        <path d="M10 3l6 8h-4v6H8v-6H4l6-8z" />
      </svg>
      {Math.abs(value)}% {suffix}
    </span>
  );
}

function formatNumber(value: number): string {
  return new Intl.NumberFormat('vi-VN').format(value);
}

function DashboardSkeleton() {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Card key={i} className="space-y-3">
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-8 w-32" />
            <Skeleton className="h-4 w-20" />
          </Card>
        ))}
      </div>
      <Card>
        <Skeleton className="mb-3 h-5 w-64" />
        <Skeleton className="h-80 w-full" />
      </Card>
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card>
          <Skeleton className="mb-3 h-5 w-48" />
          <Skeleton className="h-72 w-full" />
        </Card>
        <Card>
          <Skeleton className="mb-3 h-5 w-48" />
          <Skeleton className="h-72 w-full" />
        </Card>
      </div>
      <Card>
        <Skeleton className="mb-3 h-5 w-40" />
        <Skeleton className="h-48 w-full" />
      </Card>
    </div>
  );
}

export default function DashboardPage() {
  const [period, setPeriod] = useState(quarterOptions[0].value);
  const [cropId, setCropId] = useState<number | undefined>(undefined);
  const [status, setStatus] = useState<Status>('idle');
  const [data, setData] = useState<DashboardResult | null>(null);
  const [sortKey, setSortKey] = useState<SortKey>('yieldTPerHa');
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc');
  const [retryToken, setRetryToken] = useState(0);
  const [offline, setOffline] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setStatus('loading');
    getDashboard(period, cropId)
      .then((res) => {
        if (cancelled) return;
        setData(res);
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
  }, [period, cropId, retryToken]);

  const sortedRankings = useMemo(() => {
    if (!data) return [];
    const rows = [...data.districtRankings];
    rows.sort((a, b) => {
      const av = a[sortKey];
      const bv = b[sortKey];
      const cmp = typeof av === 'string' ? av.localeCompare(bv as string) : (av as number) - (bv as number);
      return sortDir === 'asc' ? cmp : -cmp;
    });
    return rows;
  }, [data, sortKey, sortDir]);

  function toggleSort(key: SortKey) {
    if (sortKey === key) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortKey(key);
      setSortDir('desc');
    }
  }

  const columns: { key: SortKey; label: string }[] = [
    { key: 'district', label: copy.dashboard.rankingColumns.district },
    { key: 'yieldTPerHa', label: copy.dashboard.rankingColumns.yield },
    { key: 'outputTons', label: copy.dashboard.rankingColumns.output },
    { key: 'diseaseCases', label: copy.dashboard.rankingColumns.diseaseCases },
  ];

  return (
    <div className="mx-auto max-w-6xl">
      <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
        <h1 className="text-2xl font-bold text-ink-primary">{copy.dashboard.title}</h1>
        <div className="flex flex-wrap gap-3">
          <Select
            className="min-h-[40px]"
            value={period}
            onChange={setPeriod}
            options={quarterOptions.map((q) => ({ value: q.value, label: q.labelVi }))}
          />
          <Select
            className="min-h-[40px]"
            value={cropId !== undefined ? String(cropId) : ''}
            onChange={(v) => setCropId(v ? Number(v) : undefined)}
            options={[
              { value: '', label: copy.dashboard.allCrops },
              ...crops.map((c) => ({ value: String(c.id), label: c.nameVi })),
            ]}
          />
        </div>
      </div>

      {status === 'loading' && <DashboardSkeleton />}

      {status === 'error' && (
        <EmptyState
          tone={offline ? 'offline' : 'error'}
          title={offline ? copy.common.backendUnreachableTitle : copy.dashboard.errorTitle}
          description={offline ? copy.common.backendUnreachableDesc : undefined}
          onRetry={() => setRetryToken((t) => t + 1)}
          retryLabel={copy.common.retry}
        />
      )}

      {status === 'success' && data && (
        <div className="space-y-6">
          {data.kpis.length === 0 ? (
            <EmptyState tone="offline" title={copy.common.empty} />
          ) : (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {data.kpis.map((kpi) => (
                <Card key={kpi.id} tint>
                  <p className="text-sm font-medium text-ink-secondary">{kpi.labelVi}</p>
                  <p className="mt-1 text-3xl font-extrabold text-ink-primary">
                    {formatNumber(kpi.value)} <span className="text-base font-semibold text-ink-secondary">{kpi.unit}</span>
                  </p>
                  <div className="mt-2 flex flex-col gap-1">
                    <DeltaLabel value={kpi.qoqDeltaPercent} suffix={copy.dashboard.qoq} />
                    <DeltaLabel value={kpi.yoyDeltaPercent} suffix={copy.dashboard.yoy} />
                  </div>
                </Card>
              ))}
            </div>
          )}

          <Card tint>
            <h2 className="mb-3 text-lg font-bold text-ink-primary">{copy.dashboard.districtYieldChartTitle}</h2>
            {data.districtYield.length === 0 ? (
              <EmptyState tone="offline" title={copy.common.empty} />
            ) : (
              <div className="h-80 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={data.districtYield} margin={{ top: 8, right: 8, left: 0, bottom: 0 }} barGap={4}>
                    <CartesianGrid stroke="#e1e0d9" vertical={false} />
                    <XAxis dataKey="district" tick={{ fontSize: 12, fill: '#898781' }} stroke="#c3c2b7" interval={0} angle={-20} textAnchor="end" height={60} />
                    <YAxis tick={{ fontSize: 12, fill: '#898781' }} stroke="#c3c2b7" width={48} />
                    <Tooltip isAnimationActive={false} contentStyle={{ borderRadius: 8, borderColor: '#e1e0d9', fontSize: 13 }} />
                    <Legend wrapperStyle={{ fontSize: 13 }} />
                    <Bar dataKey="currentYieldTPerHa" name={copy.dashboard.currentPeriod} fill="#16a34a" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="previousYieldTPerHa" name={copy.dashboard.previousPeriod} fill="#a3b18a" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
          </Card>

          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            <Card tint>
              <h2 className="mb-3 text-lg font-bold text-ink-primary">{copy.dashboard.diseaseCasesChartTitle}</h2>
              {data.diseaseCases.length === 0 ? (
                <EmptyState tone="offline" title={copy.common.empty} />
              ) : (
                <div className="h-72 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={data.diseaseCases} layout="vertical" margin={{ top: 8, right: 16, left: 8, bottom: 0 }}>
                      <CartesianGrid stroke="#e1e0d9" horizontal={false} />
                      <XAxis type="number" tick={{ fontSize: 12, fill: '#898781' }} stroke="#c3c2b7" />
                      <YAxis
                        type="category"
                        dataKey="diseaseName"
                        tick={{ fontSize: 12, fill: '#898781' }}
                        stroke="#c3c2b7"
                        width={110}
                      />
                      <Tooltip isAnimationActive={false} contentStyle={{ borderRadius: 8, borderColor: '#e1e0d9', fontSize: 13 }} />
                      <Bar dataKey="cases" name={copy.dashboard.rankingColumns.diseaseCases} radius={[0, 4, 4, 0]}>
                        {data.diseaseCases.map((entry, i) => (
                          <Cell key={entry.diseaseName} fill={seriesPalette[i % seriesPalette.length]} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}
            </Card>

            <Card tint>
              <h2 className="mb-3 text-lg font-bold text-ink-primary">{copy.dashboard.diseaseTrendChartTitle}</h2>
              {data.diseaseTrend.length === 0 ? (
                <EmptyState tone="offline" title={copy.common.empty} />
              ) : (
                <div className="h-72 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={data.diseaseTrend} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
                      <CartesianGrid stroke="#e1e0d9" vertical={false} />
                      <XAxis dataKey="quarterLabel" tick={{ fontSize: 12, fill: '#898781' }} stroke="#c3c2b7" />
                      <YAxis tick={{ fontSize: 12, fill: '#898781' }} stroke="#c3c2b7" width={48} />
                      <Tooltip isAnimationActive={false} contentStyle={{ borderRadius: 8, borderColor: '#e1e0d9', fontSize: 13 }} />
                      <Line type="monotone" dataKey="cases" stroke="#d97706" strokeWidth={2} dot={{ r: 4 }} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              )}
            </Card>
          </div>

          <Card tint>
            <h2 className="mb-3 text-lg font-bold text-ink-primary">{copy.dashboard.rankingTableTitle}</h2>
            {sortedRankings.length === 0 ? (
              <EmptyState tone="offline" title={copy.common.empty} />
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full min-w-[480px] border-collapse text-left">
                  <thead>
                    <tr className="border-b border-line-border">
                      <th className="px-3 py-2 text-sm font-semibold text-ink-secondary">{copy.dashboard.rankingColumns.rank}</th>
                      {columns.map((col) => (
                        <th key={col.key} className="px-3 py-2 text-sm font-semibold text-ink-secondary">
                          <button
                            type="button"
                            className="flex items-center gap-1 hover:text-ink-primary"
                            onClick={() => toggleSort(col.key)}
                          >
                            {col.label}
                            {sortKey === col.key && <span>{sortDir === 'asc' ? '▲' : '▼'}</span>}
                          </button>
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {sortedRankings.map((row) => (
                      <tr key={row.district} className="border-b border-line-grid last:border-0">
                        <td className="px-3 py-2 text-base text-ink-secondary">{row.rank}</td>
                        <td className="px-3 py-2 text-base font-medium text-ink-primary">{row.district}</td>
                        <td className="px-3 py-2 text-base tabular-nums text-ink-primary">{row.yieldTPerHa}</td>
                        <td className="px-3 py-2 text-base tabular-nums text-ink-primary">{formatNumber(row.outputTons)}</td>
                        <td className="px-3 py-2 text-base tabular-nums text-ink-primary">{row.diseaseCases}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Card>
        </div>
      )}
    </div>
  );
}
