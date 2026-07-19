'use client';

import { useEffect, useMemo, useState } from 'react';
import {
  Area,
  CartesianGrid,
  ComposedChart,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { Card } from '@/components/ui/Card';
import { Spinner } from '@/components/ui/Spinner';
import { EmptyState } from '@/components/ui/EmptyState';
import { copy } from '@/constants/copy';
import { ApiError, getMarketPrice } from '@/lib/api';
import { crops } from '@/constants/crops';
import type { MarketPriceResult } from '@/types/api';

type Status = 'idle' | 'loading' | 'success' | 'error';

// 1 điểm dữ liệu trên biểu đồ ComposedChart bên dưới. `price` (lịch sử thực tế) và
// `forecastPrice` (dự báo) tách riêng 2 trường vì Recharts vẽ chúng thành 2 đường
// khác nhau (liền nét vs đứt nét) trên CÙNG 1 trục thời gian.
interface ChartRow {
  date: string;
  price?: number;
  forecastPrice?: number;
  band?: [number, number]; // [cận dưới, cận trên] khoảng tin cậy dự báo, vẽ dạng dải mờ
}

function formatDateShort(iso: string): string {
  const d = new Date(iso);
  return `${d.getDate()}/${d.getMonth() + 1}`;
}

function formatVnd(value: number): string {
  return new Intl.NumberFormat('vi-VN').format(value);
}

// Trang giá thị trường: chọn loại cây trồng (tab), xem giá hiện tại + biểu đồ lịch sử/dự báo.
export default function PricesPage() {
  const [cropId, setCropId] = useState(crops[0].id);
  const [status, setStatus] = useState<Status>('idle');
  const [data, setData] = useState<MarketPriceResult | null>(null);
  const [retryToken, setRetryToken] = useState(0);
  const [offline, setOffline] = useState(false);

  // Gọi lại API mỗi khi đổi tab cây trồng (cropId) hoặc bấm nút "Thử lại" (retryToken
  // tăng lên để ép effect chạy lại dù cropId không đổi). Cờ `cancelled` để bỏ qua kết
  // quả trả về TRỄ của 1 lần gọi cũ (vd đổi tab liên tục) - tránh hiển thị nhầm dữ liệu.
  useEffect(() => {
    let cancelled = false;
    setStatus('loading');
    getMarketPrice(cropId)
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
  }, [cropId, retryToken]);

  // Ghép dữ liệu lịch sử (data.history) và dự báo (data.forecast) thành 1 mảng liên
  // tục để 2 đường trên biểu đồ NỐI LIỀN nhau tại điểm giao, thay vì bị đứt quãng.
  // Cách làm: điểm lịch sử cuối cùng được nhân đôi vai trò - vừa là điểm kết thúc của
  // đường "price" (lịch sử), vừa là điểm bắt đầu của đường "forecastPrice" (dự báo) -
  // gọi là "bridgeRow" (điểm nối). Nếu không có bridgeRow, 2 đường sẽ có khoảng hở.
  // bridgeRow chỉ set `price` (không set `forecastPrice`/band) để tooltip tại điểm
  // giao chỉ hiển thị dòng "Giá lịch sử" - tránh bị trùng 2 dòng "Giá dự báo".
  const chartData: ChartRow[] = useMemo(() => {
    if (!data || data.history.length === 0) return [];
    const historyRows: ChartRow[] = data.history.map((p) => ({ date: p.date, price: p.price }));
    const lastHistory = data.history[data.history.length - 1];
    const bridgeRow: ChartRow = {
      date: lastHistory.date,
      price: lastHistory.price,
    };
    // Bỏ qua điểm dự báo NaN (lỗi model) để không hiển thị giá trị NaN trên biểu đồ
    // và tooltip.
    const forecastRows: ChartRow[] = data.forecast
      .filter((p) => Number.isFinite(p.price))
      .map((p) => ({
        date: p.date,
        forecastPrice: p.price,
        band: [p.lowerBand, p.upperBand],
      }));
    // Bỏ điểm lịch sử cuối cùng ở historyRows (slice(0, -1)) vì đã có bản sao của nó
    // trong bridgeRow rồi - tránh trùng lặp 1 điểm trên biểu đồ.
    return [...historyRows.slice(0, -1), bridgeRow, ...forecastRows];
  }, [data]);

  const isUp = (data?.change7dPercent ?? 0) >= 0;

  return (
    <div className="mx-auto max-w-md px-4 py-5">
      <h1 className="mb-4 text-2xl font-bold text-ink-primary">{copy.prices.title}</h1>

      <div role="tablist" aria-label={copy.forecast.cropLabel} className="mb-4 flex gap-2">
        {crops.map((c) => {
          const isSelected = c.id === cropId;
          return (
            <button
              key={c.id}
              type="button"
              role="tab"
              aria-selected={isSelected}
              onClick={() => setCropId(c.id)}
              className={`min-h-[44px] flex-1 rounded-xl px-3 py-2 text-sm font-semibold transition-colors ${
                isSelected
                  ? 'bg-brand-600 text-white'
                  : 'border border-line-border bg-white text-ink-primary hover:border-brand-300 hover:bg-brand-50'
              }`}
            >
              {c.nameVi}
            </button>
          );
        })}
      </div>

      {status === 'loading' && <Spinner label={copy.common.loading} />}

      {status === 'error' && (
        <EmptyState
          tone={offline ? 'offline' : 'error'}
          title={offline ? copy.common.backendUnreachableTitle : copy.prices.errorTitle}
          description={offline ? copy.common.backendUnreachableDesc : undefined}
          onRetry={() => setRetryToken((t) => t + 1)}
          retryLabel={copy.common.retry}
        />
      )}

      {status === 'success' && data && (
        <div className="space-y-4">
          <Card tint>
            <p className="text-base text-ink-secondary">{copy.prices.currentPriceLabel}</p>
            <p className="text-3xl font-extrabold text-ink-primary">
              {formatVnd(data.currentPrice)} <span className="text-lg font-semibold text-ink-secondary">{data.unit}</span>
            </p>
            <div className="mt-2 flex items-center gap-2">
              <span
                className={`inline-flex items-center gap-1 text-base font-bold ${isUp ? 'text-[#006300]' : 'text-status-critical'}`}
              >
                <svg viewBox="0 0 20 20" fill="currentColor" className={`h-4 w-4 ${isUp ? '' : 'rotate-180'}`}>
                  <path d="M10 3l6 8h-4v6H8v-6H4l6-8z" />
                </svg>
                {Math.abs(data.change7dPercent)}% (thay đổi {data.changeDays} ngày)
              </span>
            </div>
            <p className="mt-2 text-base font-medium text-ink-primary">{data.trendLabel}</p>
            <p className="mt-1 text-sm text-ink-muted">{copy.prices.disclaimer}</p>
          </Card>

          {chartData.length === 0 ? (
            <EmptyState tone="offline" title={copy.common.empty} />
          ) : (
            <Card tint>
              <div className="mb-2 flex items-center gap-4 text-sm">
                <span className="flex items-center gap-1.5 text-ink-secondary">
                  <span className="h-0.5 w-4 bg-brand-600" /> {copy.prices.chartLegendHistory}
                </span>
                <span className="flex items-center gap-1.5 text-ink-secondary">
                  <span className="h-0.5 w-4 border-t-2 border-dashed border-[#d97706]" /> {copy.prices.chartLegendForecast}
                </span>
                <span className="flex items-center gap-1.5 text-ink-secondary">
                  <span className="h-2.5 w-2.5 rounded-sm bg-[#d97706]/25" /> {copy.prices.confidenceBandLabel}
                </span>
              </div>
              <div className="h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <ComposedChart data={chartData} margin={{ top: 8, right: 16, left: -16, bottom: 0 }}>
                    <CartesianGrid stroke="#e1e0d9" vertical={false} />
                    <XAxis
                      dataKey="date"
                      tickFormatter={formatDateShort}
                      tick={{ fontSize: 12, fill: '#898781' }}
                      stroke="#c3c2b7"
                      minTickGap={40}
                    />
                    <YAxis
                      tick={{ fontSize: 12, fill: '#898781' }}
                      stroke="#c3c2b7"
                      width={56}
                      domain={['auto', 'auto']}
                      tickFormatter={(v: number) => formatVnd(v)}
                    />
                    <Tooltip
                      // isAnimationActive={false}: tắt hiệu ứng trượt mặc định của
                      // Recharts khi rê chuột - nếu không tắt, tooltip sẽ "trễ" 1 nhịp
                      // so với vị trí con trỏ, gây cảm giác giật/chậm khi tương tác.
                      isAnimationActive={false}
                      formatter={(value, name) => [
                        `${formatVnd(Number(value))} ${data.unit}`,
                        name === 'price' ? copy.prices.chartLegendHistory : copy.prices.chartLegendForecast,
                      ]}
                      labelFormatter={(label) => new Date(String(label)).toLocaleDateString('vi-VN')}
                      contentStyle={{ borderRadius: 8, borderColor: '#e1e0d9', fontSize: 13 }}
                    />
                    <Area
                      dataKey="band"
                      stroke="none"
                      fill="#d97706"
                      fillOpacity={0.15}
                      isAnimationActive={false}
                      connectNulls
                    />
                    <Line
                      type="monotone"
                      dataKey="price"
                      stroke="#16a34a"
                      strokeWidth={2}
                      dot={false}
                      isAnimationActive={false}
                      connectNulls
                    />
                    <Line
                      type="monotone"
                      dataKey="forecastPrice"
                      stroke="#d97706"
                      strokeWidth={2}
                      strokeDasharray="5 4"
                      dot={false}
                      isAnimationActive={false}
                      connectNulls
                    />
                  </ComposedChart>
                </ResponsiveContainer>
              </div>
            </Card>
          )}
        </div>
      )}
    </div>
  );
}
