import type { ReactNode } from 'react';

export type BadgeTone = 'good' | 'warning' | 'serious' | 'critical' | 'neutral';

interface BadgeProps {
  tone: BadgeTone;
  label: string;
  icon?: ReactNode;
}

const toneClasses: Record<BadgeTone, string> = {
  good: 'bg-status-good/10 text-status-good border-status-good/30',
  warning: 'bg-status-warning/15 text-[#8a5a00] border-status-warning/40',
  serious: 'bg-status-serious/15 text-[#a04321] border-status-serious/40',
  critical: 'bg-status-critical/10 text-status-critical border-status-critical/30',
  neutral: 'bg-ink-muted/10 text-ink-secondary border-ink-muted/30',
};

const defaultIcons: Record<BadgeTone, ReactNode> = {
  good: (
    <svg viewBox="0 0 20 20" fill="currentColor" className="h-4 w-4" aria-hidden="true">
      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.7-9.3a1 1 0 00-1.4-1.4L9 10.6 7.7 9.3a1 1 0 00-1.4 1.4l2 2a1 1 0 001.4 0l4-4z" clipRule="evenodd" />
    </svg>
  ),
  warning: (
    <svg viewBox="0 0 20 20" fill="currentColor" className="h-4 w-4" aria-hidden="true">
      <path fillRule="evenodd" d="M8.3 3.3a2 2 0 013.4 0l6.4 11.1A2 2 0 0116.4 17H3.6a2 2 0 01-1.7-2.6L8.3 3.3zM10 7a1 1 0 011 1v3a1 1 0 11-2 0V8a1 1 0 011-1zm0 7a1 1 0 100 2 1 1 0 000-2z" clipRule="evenodd" />
    </svg>
  ),
  serious: (
    <svg viewBox="0 0 20 20" fill="currentColor" className="h-4 w-4" aria-hidden="true">
      <path fillRule="evenodd" d="M8.3 3.3a2 2 0 013.4 0l6.4 11.1A2 2 0 0116.4 17H3.6a2 2 0 01-1.7-2.6L8.3 3.3zM10 7a1 1 0 011 1v3a1 1 0 11-2 0V8a1 1 0 011-1zm0 7a1 1 0 100 2 1 1 0 000-2z" clipRule="evenodd" />
    </svg>
  ),
  critical: (
    <svg viewBox="0 0 20 20" fill="currentColor" className="h-4 w-4" aria-hidden="true">
      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.7 7.3a1 1 0 011.4 0L10 7.6l-.1-.3a1 1 0 011.4 1.4L11 9l.3.3a1 1 0 01-1.4 1.4L10 10.4l-.3.3a1 1 0 01-1.4-1.4L9 9l-.3-.3a1 1 0 010-1.4z" clipRule="evenodd" />
    </svg>
  ),
  neutral: (
    <svg viewBox="0 0 20 20" fill="currentColor" className="h-4 w-4" aria-hidden="true">
      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0 1 1 0 002 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
    </svg>
  ),
};

export function Badge({ tone, label, icon }: BadgeProps) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-sm font-semibold ${toneClasses[tone]}`}
    >
      {icon ?? defaultIcons[tone]}
      {label}
    </span>
  );
}
