// Khối "xương" nhấp nháy (placeholder) hiển thị khi đang chờ dữ liệu tải về, thay cho
// spinner ở những màn có bố cục phức tạp (dashboard) để tránh giật layout khi dữ liệu
// về xong. Truyền className để định kích thước khối (vd h-4 w-24) mô phỏng nội dung thật.
interface SkeletonProps {
  className?: string;
}

export function Skeleton({ className = '' }: SkeletonProps) {
  return <div className={`animate-pulse rounded-lg bg-line-grid ${className}`} aria-hidden="true" />;
}
