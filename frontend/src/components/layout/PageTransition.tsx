'use client';

import { useState, type ReactNode } from 'react';
import { usePathname } from 'next/navigation';

const tabOrder = ['/scan', '/forecast', '/prices'];

interface PageTransitionProps {
  children: ReactNode;
}

export function PageTransition({ children }: PageTransitionProps) {
  const pathname = usePathname();
  const [prevPathname, setPrevPathname] = useState(pathname);
  const [direction, setDirection] = useState<'forward' | 'back'>('forward');

  if (pathname !== prevPathname) {
    const prevIndex = tabOrder.indexOf(prevPathname);
    const nextIndex = tabOrder.indexOf(pathname);
    if (prevIndex !== -1 && nextIndex !== -1 && nextIndex !== prevIndex) {
      setDirection(nextIndex > prevIndex ? 'forward' : 'back');
    }
    setPrevPathname(pathname);
  }

  return (
    <div key={pathname} className={direction === 'forward' ? 'animate-slide-in-right' : 'animate-slide-in-left'}>
      {children}
    </div>
  );
}
