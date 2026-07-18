import Link from 'next/link';
import type { ReactNode } from 'react';
import { copy } from '@/constants/copy';
import { Logo } from '@/components/ui/Logo';

function RoleCard({
  href,
  icon,
  title,
  description,
  accentBg,
  accentText,
}: {
  href: string;
  icon: ReactNode;
  title: string;
  description: string;
  accentBg: string;
  accentText: string;
}) {
  return (
    <Link
      href={href}
      className="group flex min-h-[44px] items-center gap-4 rounded-2xl border border-line-border bg-surface p-5 shadow-sm transition-all hover:-translate-y-0.5 hover:shadow-md focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-600"
    >
      <span className={`flex h-14 w-14 shrink-0 items-center justify-center rounded-xl ${accentBg} ${accentText}`}>
        {icon}
      </span>
      <span className="flex-1">
        <span className="block text-xl font-bold text-ink-primary">{title}</span>
        <span className="block text-base text-ink-secondary">{description}</span>
      </span>
      <svg
        viewBox="0 0 20 20"
        fill="currentColor"
        className="h-5 w-5 shrink-0 text-ink-muted transition-transform group-hover:translate-x-0.5"
        aria-hidden="true"
      >
        <path fillRule="evenodd" d="M7.2 4.5a.75.75 0 011.06.03l5 5.25a.75.75 0 010 1.04l-5 5.25a.75.75 0 11-1.09-1.03L11.7 10 7.17 5.53a.75.75 0 01.03-1.03z" clipRule="evenodd" />
      </svg>
    </Link>
  );
}

export default function RolePicker() {
  return (
    <div className="relative flex min-h-svh flex-col items-center justify-center overflow-hidden px-4 py-10">
      <div
        className="pointer-events-none absolute inset-x-0 top-0 -z-10 h-96 bg-gradient-to-b from-brand-100 via-brand-50 to-transparent"
        aria-hidden="true"
      />

      <div className="mb-10 flex flex-col items-center text-center">
        <Logo markClassName="h-14 w-14" />
        <h1 className="mt-4 text-3xl font-bold text-ink-primary">{copy.rolePicker.title}</h1>
        <p className="mt-2 text-lg text-ink-secondary">{copy.rolePicker.subtitle}</p>
      </div>

      <div className="w-full max-w-md space-y-4">
        <RoleCard
          href="/scan"
          accentBg="bg-brand-100"
          accentText="text-brand-700"
          title={copy.rolePicker.farmer}
          description={copy.rolePicker.farmerDesc}
          icon={
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5} className="h-8 w-8">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 3c-3 3-6 6-6 10a6 6 0 0012 0c0-4-3-7-6-10z" />
            </svg>
          }
        />

        <RoleCard
          href="/dashboard"
          accentBg="bg-teal-600/10"
          accentText="text-teal-700"
          title={copy.rolePicker.official}
          description={copy.rolePicker.officialDesc}
          icon={
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5} className="h-8 w-8">
              <path strokeLinecap="round" strokeLinejoin="round" d="M4 19V10m6 9V5m6 14v-7" />
            </svg>
          }
        />
      </div>
    </div>
  );
}
