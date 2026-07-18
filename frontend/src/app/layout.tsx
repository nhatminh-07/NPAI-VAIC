import type { Metadata, Viewport } from 'next';
import type { ReactNode } from 'react';
import { Be_Vietnam_Pro } from 'next/font/google';
import { copy } from '@/constants/copy';
import { ChatWidget } from '@/components/chat/ChatWidget';
import './globals.css';

// Font chữ dùng cho toàn app, có hỗ trợ bộ chữ tiếng Việt (subset "vietnamese") để
// dấu câu hiển thị đúng và đẹp.
const beVietnamPro = Be_Vietnam_Pro({
  subsets: ['latin', 'vietnamese'],
  weight: ['400', '500', '600', '700', '800'],
  variable: '--font-be-vietnam-pro',
  display: 'swap',
});

export const metadata: Metadata = {
  title: copy.appName,
  description: copy.rolePicker.subtitle,
  icons: {
    icon: '/icon.png',
  },
};

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
};

// Layout gốc, bọc TẤT CẢ các trang (kể cả màn chọn vai trò, trang nông dân, trang cán
// bộ). Đặt ChatWidget ở đây (chứ không phải trong từng shell riêng) để trợ lý AI luôn
// hiện diện ở mọi trang, không phụ thuộc người dùng đang ở vai trò nào.
export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="vi" className={beVietnamPro.variable}>
      <body>
        {children}
        <ChatWidget />
      </body>
    </html>
  );
}
