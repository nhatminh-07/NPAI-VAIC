import type { HTMLAttributes, ReactNode } from 'react';

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
  /** Subtle green gradient wash. Leave off for cards that set their own semantic bg-* tint. */
  tint?: boolean;
}

export function Card({ children, className = '', tint = false, ...rest }: CardProps) {
  return (
    <div
      className={`rounded-2xl border border-line-border ${tint ? 'bg-gradient-to-br from-surface to-brand-50/40' : 'bg-surface'} p-4 shadow-sm transition-shadow hover:shadow-md ${className}`}
      {...rest}
    >
      {children}
    </div>
  );
}
