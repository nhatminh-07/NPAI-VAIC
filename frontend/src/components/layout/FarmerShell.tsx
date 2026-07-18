'use client';

import type { ReactNode } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { copy } from '@/constants/copy';
import { Logo } from '@/components/ui/Logo';
import { PageTransition } from '@/components/layout/PageTransition';

// Khung giao diện dùng chung cho các trang dành cho NÔNG DÂN (/scan, /forecast,
// /prices) - dạng mobile-first: header cố định phía trên, thanh điều hướng (tab bar)
// cố định phía dưới, nội dung trang cuộn ở giữa. Áp dụng qua app/(farmer)/layout.tsx
// (route group "(farmer)" trong Next.js App Router).
interface FarmerShellProps {
  children: ReactNode;
}

// Danh sách tab điều hướng dưới cùng, đúng theo thứ tự hiển thị trái→phải. Thứ tự này
// cũng được PageTransition.tsx dùng để tính chiều trượt (trượt phải khi chuyển sang
// tab bên phải, trượt trái khi quay lại tab bên trái).
const tabs = [
  {
    to: '/scan',
    label: copy.nav.scan,
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} className="h-6 w-6">
        <path strokeLinecap="round" strokeLinejoin="round" d="M4 8V6a2 2 0 012-2h2M20 8V6a2 2 0 00-2-2h-2M4 16v2a2 2 0 002 2h2m10-4v2a2 2 0 01-2 2h-2" />
        <circle cx="12" cy="12" r="3.5" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    ),
  },
  {
    to: '/forecast',
    label: copy.nav.forecast,
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} className="h-6 w-6">
        <path strokeLinecap="round" strokeLinejoin="round" d="M3 17l5-5 4 4 8-9M20 7v5M20 7h-5" />
      </svg>
    ),
  },
  {
    to: '/prices',
    label: copy.nav.prices,
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} className="h-6 w-6">
        <line x1="12" y1="2" x2="12" y2="22" strokeLinecap="round" />
        <path strokeLinecap="round" strokeLinejoin="round" d="M17 5H9.5a3.5 3.5 0 000 7h5a3.5 3.5 0 010 7H6" />
      </svg>
    ),
  },
];

export function FarmerShell({ children }: FarmerShellProps) {
  const pathname = usePathname();

  return (
    <div className="flex min-h-svh flex-col bg-plane">
      <header className="flex items-center justify-between border-b border-line-border bg-gradient-to-r from-surface/90 to-brand-50/70 px-4 py-3 backdrop-blur-sm">
        <Logo withWordmark />
        <Link href="/" className="min-h-[44px] px-2 py-2 text-sm font-medium text-brand-700">
          {copy.nav.switchRole}
        </Link>
      </header>
      <main className="flex-1 overflow-x-hidden overflow-y-auto pb-24">
        <PageTransition>{children}</PageTransition>
      </main>
      <nav className="fixed inset-x-0 bottom-0 z-10 border-t border-line-border bg-gradient-to-r from-surface/95 to-brand-50/60 backdrop-blur-sm">
        <div className="mx-auto flex max-w-md items-stretch justify-around">
          {tabs.map((tab) => {
            const isActive = pathname === tab.to;
            return (
              <Link
                key={tab.to}
                href={tab.to}
                aria-current={isActive ? 'page' : undefined}
                className={`relative flex min-h-[64px] flex-1 flex-col items-center justify-center gap-1 text-sm font-medium transition-colors ${
                  isActive ? 'text-brand-600' : 'text-ink-muted'
                }`}
              >
                {isActive && <span className="absolute top-0 h-0.5 w-8 rounded-full bg-brand-600" />}
                {tab.icon}
                {tab.label}
              </Link>
            );
          })}
        </div>
      </nav>
    </div>
  );
}
