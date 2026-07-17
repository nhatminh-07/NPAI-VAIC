import type { ButtonHTMLAttributes, ReactNode } from 'react';

type Variant = 'primary' | 'secondary' | 'ghost';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  fullWidth?: boolean;
  children: ReactNode;
}

const variantClasses: Record<Variant, string> = {
  primary: 'bg-series-1 text-white hover:bg-[#2166b8] disabled:bg-line-axis',
  secondary: 'bg-white text-ink-primary border border-line-border hover:bg-plane disabled:text-ink-muted',
  ghost: 'bg-transparent text-series-1 hover:bg-plane disabled:text-ink-muted',
};

export function Button({ variant = 'primary', fullWidth, className = '', children, ...rest }: ButtonProps) {
  return (
    <button
      className={`inline-flex items-center justify-center gap-2 rounded-xl px-5 py-3 min-h-[44px] text-base font-semibold transition-colors disabled:cursor-not-allowed ${variantClasses[variant]} ${fullWidth ? 'w-full' : ''} ${className}`}
      {...rest}
    >
      {children}
    </button>
  );
}
