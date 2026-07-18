'use client';

import type { ReactNode } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { copy } from '@/constants/copy';
import { Logo } from '@/components/ui/Logo';
import { PageTransition } from '@/components/layout/PageTransition';

interface FarmerShellProps {
  children: ReactNode;
}

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
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 3v18m0 0c-2.2 0-4-1.1-4-2.5M12 21c2.2 0 4-1.1 4-2.5M12 3c2.2 0 4 1.1 4 2.5S14.2 8 12 8s-4 1.1-4 2.5S9.8 13 12 13s4 1.1 4 2.5" />
      </svg>
    ),
  },
];

export function FarmerShell({ children }: FarmerShellProps) {
  const pathname = usePathname();

  return (
    <div className="flex min-h-svh flex-col bg-plane">
      <header className="flex items-center justify-between border-b border-line-border bg-surface/90 px-4 py-3 backdrop-blur-sm">
        <Logo withWordmark />
        <Link href="/" className="min-h-[44px] px-2 py-2 text-sm font-medium text-brand-700">
          {copy.nav.switchRole}
        </Link>
      </header>
      <main className="flex-1 overflow-x-hidden overflow-y-auto pb-24">
        <PageTransition>{children}</PageTransition>
      </main>
      <nav className="fixed inset-x-0 bottom-0 z-10 border-t border-line-border bg-surface/95 backdrop-blur-sm">
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
