import type { ReactElement } from 'react';
import { Button } from './Button';
import { Card } from './Card';

type Tone = 'error' | 'offline';

interface EmptyStateProps {
  title: string;
  description?: string;
  tone?: Tone;
  onRetry?: () => void;
  retryLabel?: string;
  className?: string;
}

const toneIcon: Record<Tone, ReactElement> = {
  error: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5} className="h-10 w-10 text-status-critical">
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v4m0 4h.01M10.3 3.9L2.6 17.1a1.8 1.8 0 001.6 2.7h15.6a1.8 1.8 0 001.6-2.7L13.7 3.9a1.8 1.8 0 00-3.4 0z" />
    </svg>
  ),
  offline: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5} className="h-10 w-10 text-ink-muted">
      <path strokeLinecap="round" strokeLinejoin="round" d="M3 3l18 18M9.2 9.2A5 5 0 006 18h11m2.5-3.3A4.5 4.5 0 0016 7a6 6 0 00-9.6-2.1" />
    </svg>
  ),
};

const toneCardClass: Record<Tone, string> = {
  error: 'border-status-critical/40 bg-status-critical/5',
  offline: 'border-line-border bg-plane',
};

export function EmptyState({ title, description, tone = 'error', onRetry, retryLabel, className = '' }: EmptyStateProps) {
  return (
    <Card className={`flex flex-col items-center gap-3 py-8 text-center ${toneCardClass[tone]} ${className}`}>
      {toneIcon[tone]}
      <p className="text-base font-semibold text-ink-primary">{title}</p>
      {description && <p className="max-w-sm text-sm text-ink-secondary">{description}</p>}
      {onRetry && (
        <Button variant="secondary" className="mt-1" onClick={onRetry}>
          {retryLabel ?? 'Thử lại'}
        </Button>
      )}
    </Card>
  );
}
