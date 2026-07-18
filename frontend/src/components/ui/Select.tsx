'use client';

import { useEffect, useRef, useState } from 'react';

export interface SelectOption {
  value: string;
  label: string;
}

interface SelectProps {
  id?: string;
  value: string;
  onChange: (value: string) => void;
  options: SelectOption[];
  className?: string;
  'aria-label'?: string;
}

export function Select({ id, value, onChange, options, className = '', ...rest }: SelectProps) {
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const selected = options.find((opt) => opt.value === value);

  useEffect(() => {
    if (!open) return;
    function handlePointerDown(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === 'Escape') setOpen(false);
    }
    document.addEventListener('mousedown', handlePointerDown);
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('mousedown', handlePointerDown);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [open]);

  return (
    <div ref={containerRef} className={`relative ${className}`}>
      <button
        id={id}
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-haspopup="listbox"
        aria-expanded={open}
        {...rest}
        className="flex h-full w-full cursor-pointer items-center justify-between gap-2 rounded-lg border border-line-axis bg-white py-2 pl-3 pr-3 text-base text-ink-primary transition-colors hover:border-brand-300 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/30"
      >
        <span className="truncate">{selected?.label ?? ''}</span>
        <svg
          viewBox="0 0 20 20"
          fill="none"
          stroke="currentColor"
          strokeWidth={1.5}
          className={`h-4 w-4 shrink-0 text-ink-muted transition-transform ${open ? 'rotate-180' : ''}`}
          aria-hidden="true"
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M5 7.5l5 5 5-5" />
        </svg>
      </button>

      {open && (
        <ul
          role="listbox"
          aria-activedescendant={selected ? `${id ?? 'select'}-opt-${selected.value}` : undefined}
          className="absolute left-0 top-full z-20 mt-1 max-h-60 w-full min-w-max overflow-auto rounded-lg border border-line-border bg-white py-1 shadow-lg"
        >
          {options.map((opt) => {
            const isSelected = opt.value === value;
            return (
              <li
                key={opt.value}
                id={`${id ?? 'select'}-opt-${opt.value}`}
                role="option"
                aria-selected={isSelected}
                onClick={() => {
                  onChange(opt.value);
                  setOpen(false);
                }}
                className={`cursor-pointer whitespace-nowrap px-3 py-2 text-base transition-colors ${
                  isSelected ? 'bg-brand-50 font-semibold text-brand-700' : 'text-ink-primary hover:bg-brand-50/70'
                }`}
              >
                {opt.label}
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
