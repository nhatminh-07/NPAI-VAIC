'use client';

import type { ReactNode } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { copy } from '@/constants/copy';
import { Logo } from '@/components/ui/Logo';

// Khung giao diện dùng chung cho các trang dành cho CÁN BỘ NÔNG NGHIỆP (/dashboard,
// /disease-report) - dạng desktop: thanh điều hướng cố định bên trái (sidebar), nội
// dung trang cuộn độc lập bên phải. Áp dụng qua app/(officer)/layout.tsx.
interface OfficerShellProps {
  children: ReactNode;
}

// Danh sách mục điều hướng trong sidebar. Thêm trang mới cho cán bộ thì thêm vào đây.
const navItems = [
  {
    to: '/dashboard',
    label: copy.nav.dashboard,
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} className="h-5 w-5">
        <path strokeLinecap="round" strokeLinejoin="round" d="M4 19V10m6 9V5m6 14v-7" />
      </svg>
    ),
  },
  {
    to: '/disease-report',
    label: copy.nav.diseaseReport,
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} className="h-5 w-5">
        <path strokeLinecap="round" strokeLinejoin="round" d="M9 3v2m6-2v2M6 7h12l-1 12a2 2 0 01-2 2H9a2 2 0 01-2-2L6 7zM9.5 11l2 2 3-3" />
      </svg>
    ),
  },
];

export function OfficerShell({ children }: OfficerShellProps) {
  const pathname = usePathname();

  return (
    // Quan trọng: `h-svh overflow-hidden` (thay vì min-h-svh) để container này có
    // chiều cao CỐ ĐỊNH bằng màn hình. Nhờ đó sidebar luôn đứng yên (nút "Đổi vai trò"
    // luôn thấy được), còn nội dung chính bên phải tự cuộn riêng qua overflow-y-auto ở
    // <main>. Nếu đổi lại thành min-h-svh, cả trang sẽ cuộn chung và sidebar bị cuốn
    // theo khi nội dung dashboard dài.
    <div className="flex h-svh overflow-hidden bg-plane">
      <aside className="relative flex h-full w-64 shrink-0 flex-col border-r border-line-border bg-gradient-to-b from-surface to-brand-50/30">
        <span className="absolute inset-y-0 left-0 w-1 bg-gradient-to-b from-brand-500 via-teal-600 to-brand-700" />
        <div className="shrink-0 border-b border-line-border px-5 py-5">
          <Logo withWordmark />
        </div>
        <nav className="flex-1 space-y-1 overflow-y-auto px-3 py-4">
          {navItems.map((item) => {
            const isActive = pathname === item.to;
            return (
              <Link
                key={item.to}
                href={item.to}
                aria-current={isActive ? 'page' : undefined}
                className={`flex min-h-[44px] items-center gap-2 rounded-lg px-3 py-2 text-base font-medium transition-colors ${
                  isActive ? 'bg-teal-600/10 text-teal-700' : 'text-ink-secondary hover:bg-plane'
                }`}
              >
                {item.icon}
                {item.label}
              </Link>
            );
          })}
        </nav>
        <div className="shrink-0 border-t border-line-border px-3 py-4">
          <Link
            href="/"
            className="flex min-h-[44px] items-center gap-2 rounded-lg px-3 py-2 text-base font-medium text-ink-muted hover:bg-plane"
          >
            {copy.nav.switchRole}
          </Link>
        </div>
      </aside>
      <main className="min-w-0 flex-1 overflow-y-auto px-8 py-6">{children}</main>
    </div>
  );
}
