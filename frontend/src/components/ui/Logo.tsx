import Image from 'next/image';
import { copy } from '@/constants/copy';

// Logo ứng dụng (ảnh public/icon.png), dùng ở header các trang và màn chọn vai trò.
interface LogoProps {
  withWordmark?: boolean; // true = hiển thị kèm tên app bên cạnh icon
  className?: string;
  markClassName?: string;
  /** Kích thước icon tính bằng px. Cũng chính là độ phân giải ảnh yêu cầu Next.js
   * tối ưu ra, nên khi phóng to (vd size={96} ở màn chọn vai trò) ảnh vẫn nét,
   * không bị mờ do phóng to 1 ảnh đã tối ưu ở độ phân giải nhỏ. */
  size?: number;
}

export function Logo({ withWordmark, className = '', markClassName = '', size = 28 }: LogoProps) {
  return (
    <span className={`inline-flex items-center gap-2 ${className}`}>
      <Image
        src="/icon.png"
        alt=""
        width={size}
        height={size}
        style={{ width: size, height: size }}
        className={`shrink-0 rounded-md object-contain ${markClassName}`}
      />
      {withWordmark && <span className="text-lg font-bold text-ink-primary">{copy.appName}</span>}
    </span>
  );
}
