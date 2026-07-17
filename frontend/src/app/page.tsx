import Link from 'next/link';
import type { ReactNode } from 'react';
import { copy } from '@/constants/copy';

function RoleCard({
  href,
  icon,
  title,
  description,
  accent,
}: {
  href: string;
  icon: ReactNode;
  title: string;
  description: string;
  accent: string;
}) {
  return (
    <Link
      href={href}
      className="flex min-h-[44px] items-center gap-4 rounded-2xl border border-line-border bg-surface p-4 shadow-sm transition-shadow hover:shadow-md focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-series-1"
    >
      <span className={`shrink-0 ${accent}`}>{icon}</span>
      <span>
        <span className="block text-xl font-bold text-ink-primary">{title}</span>
        <span className="block text-base text-ink-secondary">{description}</span>
      </span>
    </Link>
  );
}

export default function RolePicker() {
  return (
    <div className="flex min-h-svh flex-col items-center justify-center bg-plane px-4 py-10">
      <div className="mb-8 text-center">
        <h1 className="text-3xl font-bold text-ink-primary">{copy.rolePicker.title}</h1>
        <p className="mt-2 text-lg text-ink-secondary">{copy.rolePicker.subtitle}</p>
      </div>

      <div className="w-full max-w-md space-y-4">
        <RoleCard
          href="/scan"
          accent="text-series-1"
          title={copy.rolePicker.farmer}
          description={copy.rolePicker.farmerDesc}
          icon={
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5} className="h-10 w-10">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 3c-3 3-6 6-6 10a6 6 0 0012 0c0-4-3-7-6-10z" />
            </svg>
          }
        />

        <RoleCard
          href="/dashboard"
          accent="text-series-7"
          title={copy.rolePicker.official}
          description={copy.rolePicker.officialDesc}
          icon={
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5} className="h-10 w-10">
              <path strokeLinecap="round" strokeLinejoin="round" d="M4 19V10m6 9V5m6 14v-7" />
            </svg>
          }
        />
      </div>
    </div>
  );
}
