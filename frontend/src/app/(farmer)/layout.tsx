import type { ReactNode } from 'react';
import { FarmerShell } from '@/components/layout/FarmerShell';

// Route group "(farmer)" (dấu ngoặc = không xuất hiện trong URL): mọi trang đặt trong
// thư mục app/(farmer)/ (scan, forecast, prices) sẽ tự động được bọc trong FarmerShell.
export default function FarmerLayout({ children }: { children: ReactNode }) {
  return <FarmerShell>{children}</FarmerShell>;
}
