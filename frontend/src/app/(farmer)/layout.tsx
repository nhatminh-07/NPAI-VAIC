import type { ReactNode } from 'react';
import { FarmerShell } from '@/components/layout/FarmerShell';

export default function FarmerLayout({ children }: { children: ReactNode }) {
  return <FarmerShell>{children}</FarmerShell>;
}
