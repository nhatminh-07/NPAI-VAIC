// Vòng xoay loading đơn giản, dùng cho các thao tác chờ ngắn (đang phân tích ảnh,
// đang tính dự báo...). Với màn có nhiều khối nội dung (dashboard) nên dùng Skeleton
// thay vì Spinner để trải nghiệm mượt hơn.
interface SpinnerProps {
  label?: string;
}

export function Spinner({ label }: SpinnerProps) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-8" role="status">
      <div className="h-10 w-10 animate-spin rounded-full border-4 border-line-grid border-t-brand-600" />
      {label && <p className="text-base text-ink-secondary">{label}</p>}
    </div>
  );
}
