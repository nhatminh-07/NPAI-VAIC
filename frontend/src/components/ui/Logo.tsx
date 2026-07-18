import { copy } from '@/constants/copy';

interface LogoProps {
  withWordmark?: boolean;
  className?: string;
  markClassName?: string;
}

export function Logo({ withWordmark, className = '', markClassName = '' }: LogoProps) {
  return (
    <span className={`inline-flex items-center gap-2 ${className}`}>
      <svg
        viewBox="0 0 24 24"
        fill="none"
        className={`h-7 w-7 shrink-0 text-brand-600 ${markClassName}`}
        aria-hidden="true"
      >
        <path
          d="M12 21c-4.5-1.2-7.5-4.8-7.5-9.5C4.5 6.8 8.3 3.5 12 3c3.7.5 7.5 3.8 7.5 8.5 0 4.7-3 8.3-7.5 9.5z"
          fill="currentColor"
          fillOpacity={0.16}
        />
        <path
          d="M12 21c-4.5-1.2-7.5-4.8-7.5-9.5C4.5 6.8 8.3 3.5 12 3c3.7.5 7.5 3.8 7.5 8.5 0 4.7-3 8.3-7.5 9.5z"
          stroke="currentColor"
          strokeWidth={1.5}
          strokeLinejoin="round"
        />
        <path d="M12 21V9M12 9c0-2.5 1.8-4.5 4-5" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" />
      </svg>
      {withWordmark && <span className="text-lg font-bold text-ink-primary">{copy.appName}</span>}
    </span>
  );
}
