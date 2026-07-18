// Thanh hiển thị độ tin cậy (confidence) của model AI, dùng ở kết quả chẩn đoán bệnh.
interface ConfidenceBarProps {
  confidence: number; // 0..1
  label: string;
}

// Ngưỡng màu: >=85% xanh lá (đáng tin), 60-85% vàng (cảnh báo nhẹ), <60% đỏ (nên chụp
// lại ảnh - xem cảnh báo lowConfidenceWarning ở trang /scan).
function toneFor(confidence: number): { bar: string; text: string } {
  if (confidence >= 0.85) return { bar: 'bg-brand-600', text: 'text-brand-700' };
  if (confidence >= 0.6) return { bar: 'bg-status-warning', text: 'text-[#8a5a00]' };
  return { bar: 'bg-status-critical', text: 'text-status-critical' };
}

export function ConfidenceBar({ confidence, label }: ConfidenceBarProps) {
  const percent = Math.round(confidence * 100);
  const tone = toneFor(confidence);

  return (
    <div>
      <div className="mb-1 flex items-center justify-between text-base">
        <span className="text-ink-secondary">{label}</span>
        <span className={`font-bold ${tone.text}`}>{percent}%</span>
      </div>
      <div
        className="h-3 w-full overflow-hidden rounded-full bg-line-grid"
        role="progressbar"
        aria-valuenow={percent}
        aria-valuemin={0}
        aria-valuemax={100}
      >
        <div className={`h-full rounded-full ${tone.bar}`} style={{ width: `${percent}%` }} />
      </div>
    </div>
  );
}
