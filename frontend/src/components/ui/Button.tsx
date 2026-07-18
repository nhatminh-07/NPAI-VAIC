import type { ButtonHTMLAttributes, ReactNode } from 'react';

type Variant = 'primary' | 'secondary' | 'ghost';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  fullWidth?: boolean;
  children: ReactNode;
}

const variantClasses: Record<Variant, string> = {
  primary: 'bg-gradient-to-b from-brand-500 to-brand-600 text-white shadow-sm hover:from-brand-600 hover:to-brand-700 disabled:bg-line-axis disabled:from-line-axis disabled:to-line-axis disabled:shadow-none',
  secondary: 'bg-white text-ink-primary border border-line-border hover:border-brand-300 hover:bg-brand-50 disabled:text-ink-muted disabled:hover:bg-white',
  ghost: 'bg-transparent text-brand-700 hover:bg-brand-50 disabled:text-ink-muted',
};

export function Button({ variant = 'primary', fullWidth, className = '', children, ...rest }: ButtonProps) {
  return (
    <button
      className={`inline-flex items-center justify-center gap-2 rounded-xl px-5 py-3 min-h-[44px] text-base font-semibold transition-all active:scale-[.98] disabled:cursor-not-allowed disabled:active:scale-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-600 ${variantClasses[variant]} ${fullWidth ? 'w-full' : ''} ${className}`}
      {...rest}
    >
      {children}
    </button>
  );
}
