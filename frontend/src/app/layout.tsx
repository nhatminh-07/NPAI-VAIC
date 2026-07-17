import type { Metadata, Viewport } from 'next';
import type { ReactNode } from 'react';
import { copy } from '@/constants/copy';
import './globals.css';

export const metadata: Metadata = {
  title: copy.appName,
  description: copy.rolePicker.subtitle,
  icons: {
    icon: '/favicon.svg',
  },
};

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="vi">
      <body>{children}</body>
    </html>
  );
}
