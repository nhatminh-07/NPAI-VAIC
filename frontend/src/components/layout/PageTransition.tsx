'use client';

// Bọc nội dung trang trong FarmerShell để tạo hiệu ứng trượt (như app di động) mỗi
// khi chuyển tab dưới cùng (Chẩn đoán/Dự báo/Giá cả). Trượt sang phải khi chuyển tới
// tab bên phải trong `tabOrder`, trượt sang trái khi quay lại tab bên trái.

import { useState, type ReactNode } from 'react';
import { usePathname } from 'next/navigation';

// Thứ tự phải khớp với mảng `tabs` trong FarmerShell.tsx để tính đúng chiều trượt.
const tabOrder = ['/scan', '/forecast', '/prices'];

interface PageTransitionProps {
  children: ReactNode;
}

export function PageTransition({ children }: PageTransitionProps) {
  const pathname = usePathname();
  const [prevPathname, setPrevPathname] = useState(pathname);
  const [direction, setDirection] = useState<'forward' | 'back'>('forward');

  // So sánh pathname mới với pathname đã lưu NGAY TRONG lúc render (không dùng
  // useEffect) để chiều trượt được xác định đúng TRƯỚC khi khối bên dưới vẽ ra màn
  // hình - tránh bị "giật" 1 khung hình theo hướng cũ rồi mới sửa lại.
  if (pathname !== prevPathname) {
    const prevIndex = tabOrder.indexOf(prevPathname);
    const nextIndex = tabOrder.indexOf(pathname);
    if (prevIndex !== -1 && nextIndex !== -1 && nextIndex !== prevIndex) {
      setDirection(nextIndex > prevIndex ? 'forward' : 'back');
    }
    setPrevPathname(pathname);
  }

  // key={pathname}: buộc React tạo lại <div> mới mỗi khi đổi trang, để animation CSS
  // (animate-slide-in-*, định nghĩa ở globals.css) chạy lại từ đầu thay vì chỉ chạy
  // đúng 1 lần ở lần mount đầu tiên.
  return (
    <div key={pathname} className={direction === 'forward' ? 'animate-slide-in-right' : 'animate-slide-in-left'}>
      {children}
    </div>
  );
}
