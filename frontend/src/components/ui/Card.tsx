import type { HTMLAttributes, ReactNode } from 'react';

// Khối bo góc dùng làm "khung chứa" chung cho mọi nội dung (form, kết quả, biểu đồ...).
interface CardProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
  /** Phủ thêm 1 lớp gradient xanh lá rất nhạt cho đẹp mắt. KHÔNG bật `tint` cho các
   * Card đã tự set màu nền riêng mang ý nghĩa (vd cảnh báo màu vàng, lỗi màu đỏ) -
   * vì gradient sẽ vẽ đè lên trên, làm mất màu nền gốc đó. */
  tint?: boolean;
}

export function Card({ children, className = '', tint = false, ...rest }: CardProps) {
  return (
    <div
      className={`rounded-2xl border border-line-border ${tint ? 'bg-gradient-to-br from-surface to-brand-50/40' : 'bg-surface'} p-4 shadow-sm transition-shadow hover:shadow-md ${className}`}
      {...rest}
    >
      {children}
    </div>
  );
}
