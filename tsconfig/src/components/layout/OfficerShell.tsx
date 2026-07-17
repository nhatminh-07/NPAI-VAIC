'use client';

import type { ReactNode } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { copy } from '@/constants/copy';

interface OfficerShellProps {
  children: ReactNode;
}

export function OfficerShell({ children }: OfficerShellProps) {
  const pathname = usePathname();
  const isDashboardActive = pathname === '/dashboard';

  return (
    <div className="flex min-h-svh bg-plane">
      <aside className="flex w-64 shrink-0 flex-col border-r border-line-border bg-surface">
        <div className="border-b border-line-border px-5 py-5">
          <span className="text-lg font-bold text-ink-primary">{copy.appName}</span>
        </div>
        <nav className="flex-1 px-3 py-4">
          <Link
            href="/dashboard"
            aria-current={isDashboardActive ? 'page' : undefined}
            className={`flex min-h-[44px] items-center gap-2 rounded-lg px-3 py-2 text-base font-medium ${
              isDashboardActive ? 'bg-series-1/10 text-series-1' : 'text-ink-secondary hover:bg-plane'
            }`}
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} className="h-5 w-5">
              <path strokeLinecap="round" strokeLinejoin="round" d="M4 19V10m6 9V5m6 14v-7" />
            </svg>
            {copy.nav.dashboard}
          </Link>
        </nav>
        <div className="border-t border-line-border px-3 py-4">
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
