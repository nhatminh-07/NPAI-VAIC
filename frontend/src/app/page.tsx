import Link from 'next/link';
import Image from 'next/image';
import type { ReactNode } from 'react';
import { copy } from '@/constants/copy';
import { Logo } from '@/components/ui/Logo';

// Màn hình đầu tiên người dùng thấy: chọn vào luồng "nông dân" (/scan, dùng
// FarmerShell) hay "cán bộ nông nghiệp" (/dashboard, dùng OfficerShell). Đây KHÔNG
// phải đăng nhập thật - chỉ là điều hướng theo vai trò, không có xác thực/phân quyền.
function RoleCard({
  href,
  icon,
  title,
  description,
}: {
  href: string;
  icon: ReactNode;
  title: string;
  description: string;
}) {
  return (
    <Link
      href={href}
      className="group flex min-h-[44px] items-center gap-5 rounded-2xl border border-line-border bg-surface p-6 shadow-sm transition-all hover:-translate-y-0.5 hover:shadow-lg focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-600"
    >
      <span className="flex h-20 w-20 shrink-0 items-center justify-center">{icon}</span>
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
        <div className="relative mb-2">
          <div
            className="absolute inset-0 -z-10 scale-125 rounded-full bg-gradient-to-br from-brand-300/40 to-teal-300/30 blur-2xl"
            aria-hidden="true"
          />
          <div className="rounded-3xl border border-white/60 bg-white/70 p-4 shadow-lg shadow-brand-900/5 backdrop-blur-sm">
            <Logo size={96} markClassName="rounded-2xl drop-shadow-sm" />
          </div>
        </div>
        <h1 className="mt-4 text-3xl font-bold text-ink-primary">{copy.rolePicker.title}</h1>
        <p className="mt-2 text-lg text-ink-secondary">{copy.rolePicker.subtitle}</p>
      </div>

      <div className="w-full max-w-md space-y-4">
        <RoleCard
          href="/scan"
          title={copy.rolePicker.farmer}
          description={copy.rolePicker.farmerDesc}
          icon={
            <Image
              src="/villager.png"
              alt=""
              width={80}
              height={80}
              className="h-20 w-20 object-contain drop-shadow-md"
            />
          }
        />

        <RoleCard
          href="/dashboard"
          title={copy.rolePicker.official}
          description={copy.rolePicker.officialDesc}
          icon={
            <Image
              src="/official.png"
              alt=""
              width={80}
              height={80}
              className="h-20 w-20 object-contain drop-shadow-md"
            />
          }
        />
      </div>
    </div>
  );
}
