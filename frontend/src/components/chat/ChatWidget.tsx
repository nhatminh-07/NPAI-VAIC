'use client';

// Widget trợ lý AI (chatbot) dạng bong bóng nổi, bật/tắt được như các widget hỗ trợ khách
// hàng thông thường (Intercom/Zalo OA...). Hiển thị trên mọi trang (gắn ở root layout).
// Toàn bộ giao tiếp với backend đi qua sendChatMessage() trong src/lib/api.ts - xem chú thích
// chi tiết về API contract (POST /assistant/chat) tại đó.

import { useEffect, useRef, useState } from 'react';
import type { FormEvent } from 'react';
import { copy } from '@/constants/copy';
import { ApiError, sendChatMessage } from '@/lib/api';
import type { ChatMessage } from '@/types/api';

type Status = 'idle' | 'loading' | 'error';

export function ChatWidget() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [status, setStatus] = useState<Status>('idle');
  const [offline, setOffline] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
  }, [messages, status, open]);

  async function sendMessage(text: string) {
    const trimmed = text.trim();
    if (!trimmed || status === 'loading') return;

    const history = messages;
    const nextMessages: ChatMessage[] = [...history, { role: 'user', content: trimmed }];
    setMessages(nextMessages);
    setInput('');
    setStatus('loading');

    try {
      const res = await sendChatMessage(trimmed, history);
      setMessages([...nextMessages, { role: 'assistant', content: res.reply }]);
      setStatus('idle');
    } catch (err) {
      setOffline(err instanceof ApiError && err.offline);
      setStatus('error');
    }
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    void sendMessage(input);
  }

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-label={open ? copy.chat.close : copy.chat.open}
        aria-expanded={open}
        className="fixed bottom-24 right-4 z-40 flex h-14 w-14 items-center justify-center rounded-full bg-gradient-to-b from-brand-500 to-brand-600 text-white shadow-lg transition-transform hover:scale-105 active:scale-95 md:bottom-6"
      >
        {open ? (
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} className="h-6 w-6">
            <path strokeLinecap="round" strokeLinejoin="round" d="M6 6l12 12M18 6L6 18" />
          </svg>
        ) : (
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} className="h-6 w-6">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M21 11.5a8.38 8.38 0 01-.9 3.8 8.5 8.5 0 01-7.6 4.7 8.38 8.38 0 01-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 01-.9-3.8 8.5 8.5 0 014.7-7.6 8.38 8.38 0 013.8-.9h.5a8.48 8.48 0 018 8v.5z"
            />
          </svg>
        )}
      </button>

      {open && (
        <div className="fixed bottom-40 right-4 z-40 flex h-[28rem] w-[22rem] max-w-[calc(100vw-2rem)] flex-col overflow-hidden rounded-2xl border border-line-border bg-white shadow-xl md:bottom-24">
          <div className="flex shrink-0 items-center justify-between border-b border-line-border bg-gradient-to-r from-brand-50 to-white px-4 py-3">
            <div>
              <p className="font-bold text-ink-primary">{copy.chat.title}</p>
              <p className="text-xs text-ink-secondary">{copy.chat.subtitle}</p>
            </div>
            <button
              type="button"
              onClick={() => setOpen(false)}
              aria-label={copy.chat.close}
              className="flex h-8 w-8 items-center justify-center rounded-full text-ink-muted hover:bg-plane"
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} className="h-5 w-5">
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 6l12 12M18 6L6 18" />
              </svg>
            </button>
          </div>

          <div ref={scrollRef} className="flex-1 space-y-3 overflow-y-auto px-4 py-3">
            {messages.length === 0 && <p className="text-sm text-ink-secondary">{copy.chat.emptyHint}</p>}

            {messages.map((m, i) => (
              <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div
                  className={`max-w-[85%] whitespace-pre-wrap rounded-2xl px-3 py-2 text-sm ${
                    m.role === 'user' ? 'bg-brand-600 text-white' : 'bg-plane text-ink-primary'
                  }`}
                >
                  {m.content}
                </div>
              </div>
            ))}

            {status === 'loading' && (
              <div className="flex justify-start">
                <div className="flex items-center gap-1.5 rounded-2xl bg-plane px-3 py-2 text-sm text-ink-secondary">
                  <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-ink-muted [animation-delay:-0.3s]" />
                  <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-ink-muted [animation-delay:-0.15s]" />
                  <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-ink-muted" />
                </div>
              </div>
            )}

            {status === 'error' && (
              <p className="text-sm text-status-critical">
                {offline ? copy.common.backendUnreachableDesc : copy.chat.errorMessage}
              </p>
            )}
          </div>

          {messages.length === 0 && (
            <div className="flex shrink-0 flex-wrap gap-2 border-t border-line-border px-3 py-2">
              {copy.chat.hints.map((hint) => (
                <button
                  key={hint}
                  type="button"
                  onClick={() => void sendMessage(hint)}
                  className="rounded-full border border-brand-200 bg-brand-50 px-3 py-1.5 text-left text-xs font-medium text-brand-700 transition-colors hover:bg-brand-100"
                >
                  {hint}
                </button>
              ))}
            </div>
          )}

          <form onSubmit={handleSubmit} className="flex shrink-0 items-center gap-2 border-t border-line-border p-3">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={copy.chat.inputPlaceholder}
              aria-label={copy.chat.inputPlaceholder}
              className="min-h-[40px] flex-1 rounded-lg border border-line-axis bg-white px-3 text-sm text-ink-primary transition-colors focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/30"
            />
            <button
              type="submit"
              disabled={status === 'loading' || !input.trim()}
              aria-label={copy.chat.send}
              className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-gradient-to-b from-brand-500 to-brand-600 text-white transition-colors hover:from-brand-600 hover:to-brand-700 disabled:from-line-axis disabled:to-line-axis"
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} className="h-5 w-5">
                <path strokeLinecap="round" strokeLinejoin="round" d="M3 11l18-8-8 18-2-8-8-2z" />
              </svg>
            </button>
          </form>
        </div>
      )}
    </>
  );
}
