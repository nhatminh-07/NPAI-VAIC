'use client';

// Dropdown chọn 1 giá trị, tự vẽ lại từ đầu (không dùng thẻ <select> gốc của trình
// duyệt) để có thể chỉnh giao diện (bo góc, màu sắc, icon...) theo đúng theme của app -
// thẻ <select> gốc không cho phép style phần danh sách option khi mở ra.
// Dùng cho: chọn loại cây trồng, chọn huyện, chọn kỳ báo cáo (quý/năm)...

import { useEffect, useLayoutEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';

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

interface Position {
  top: number;
  left: number;
  width: number;
}

export function Select({ id, value, onChange, options, className = '', ...rest }: SelectProps) {
  const [open, setOpen] = useState(false);
  const [pos, setPos] = useState<Position | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const panelRef = useRef<HTMLUListElement>(null);
  const selected = options.find((opt) => opt.value === value);

  function openDropdown() {
    const rect = containerRef.current?.getBoundingClientRect();
    if (!rect) return;
    // Vị trí thô ban đầu (bám theo trigger); được chỉnh lại ngay bên dưới trước khi
    // trình duyệt vẽ khung hình, để tránh tràn ra ngoài viewport.
    setPos({ top: rect.bottom + 4, left: rect.left, width: rect.width });
    setOpen(true);
  }

  // Panel được render qua portal (position: fixed, gắn vào document.body) thay vì
  // absolute bên trong container, để không bị các ancestor có overflow-y-auto/hidden
  // (vd. <main> trong OfficerShell) cắt (clip) mất phần tràn ra ngoài khung nhìn của chúng.
  useLayoutEffect(() => {
    if (!open) return;
    const trigger = containerRef.current;
    const panel = panelRef.current;
    if (!trigger || !panel) return;

    const triggerRect = trigger.getBoundingClientRect();
    const panelRect = panel.getBoundingClientRect();
    const vw = window.innerWidth;
    const vh = window.innerHeight;
    const margin = 8;

    let left = triggerRect.left;
    if (left + panelRect.width > vw - margin) {
      left = Math.max(margin, vw - panelRect.width - margin);
    }

    let top = triggerRect.bottom + 4;
    if (top + panelRect.height > vh - margin) {
      top = triggerRect.top - panelRect.height - 4;
    }

    setPos((prev) =>
      prev && prev.top === top && prev.left === left && prev.width === triggerRect.width
        ? prev
        : { top, left, width: triggerRect.width },
    );
  }, [open]);

  // Đóng dropdown khi: bấm ra ngoài, nhấn Escape, hoặc cuộn/resize trang.
  useEffect(() => {
    if (!open) return;
    function handlePointerDown(e: MouseEvent) {
      const target = e.target as Node;
      // Lưu ý: panel được portal ra ngoài <body> (xem bên dưới), nên KHÔNG nằm trong
      // containerRef - phải kiểm tra thêm panelRef, nếu không thì bấm chọn 1 option
      // sẽ bị coi là "bấm ra ngoài" và đóng dropdown trước khi kịp xử lý click chọn.
      if (containerRef.current?.contains(target)) return;
      if (panelRef.current?.contains(target)) return;
      setOpen(false);
    }
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === 'Escape') setOpen(false);
    }
    // Đóng dropdown khi bất kỳ ancestor nào cuộn (kể cả <main> có overflow riêng) -
    // dùng capture:true vì sự kiện scroll của phần tử con không bubble lên.
    function handleScroll() {
      setOpen(false);
    }
    document.addEventListener('mousedown', handlePointerDown);
    document.addEventListener('keydown', handleKeyDown);
    document.addEventListener('scroll', handleScroll, true);
    window.addEventListener('resize', handleScroll);
    return () => {
      document.removeEventListener('mousedown', handlePointerDown);
      document.removeEventListener('keydown', handleKeyDown);
      document.removeEventListener('scroll', handleScroll, true);
      window.removeEventListener('resize', handleScroll);
    };
  }, [open]);

  return (
    <div ref={containerRef} className={`relative ${className}`}>
      <button
        id={id}
        type="button"
        onClick={() => (open ? setOpen(false) : openDropdown())}
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

      {open &&
        pos &&
        createPortal(
          <ul
            ref={panelRef}
            role="listbox"
            aria-activedescendant={selected ? `${id ?? 'select'}-opt-${selected.value}` : undefined}
            style={{ top: pos.top, left: pos.left, minWidth: pos.width }}
            className="fixed z-50 max-h-60 w-max max-w-[calc(100vw-16px)] overflow-auto rounded-lg border border-line-border bg-white py-1 shadow-lg"
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
          </ul>,
          document.body,
        )}
    </div>
  );
}
