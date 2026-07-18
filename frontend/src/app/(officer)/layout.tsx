import type { ReactNode } from 'react';
import { OfficerShell } from '@/components/layout/OfficerShell';

// Route group "(officer)": mọi trang trong app/(officer)/ (dashboard, disease-report)
// tự động được bọc trong OfficerShell (sidebar dành cho cán bộ).
export default function OfficerLayout({ children }: { children: ReactNode }) {
  return <OfficerShell>{children}</OfficerShell>;
}
