import type { HTMLAttributes, ReactNode } from 'react';

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
}

export function Card({ children, className = '', ...rest }: CardProps) {
  return (
    <div
      className={`rounded-2xl border border-line-border bg-surface p-4 shadow-sm transition-shadow hover:shadow-md ${className}`}
      {...rest}
    >
      {children}
    </div>
  );
}
