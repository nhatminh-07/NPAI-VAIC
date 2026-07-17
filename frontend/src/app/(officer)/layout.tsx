import type { ReactNode } from 'react';
import { OfficerShell } from '@/components/layout/OfficerShell';

export default function OfficerLayout({ children }: { children: ReactNode }) {
  return <OfficerShell>{children}</OfficerShell>;
}
