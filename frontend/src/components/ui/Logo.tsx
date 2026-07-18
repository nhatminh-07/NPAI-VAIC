import Image from 'next/image';
import { copy } from '@/constants/copy';

interface LogoProps {
  withWordmark?: boolean;
  className?: string;
  markClassName?: string;
}

export function Logo({ withWordmark, className = '', markClassName = '' }: LogoProps) {
  return (
    <span className={`inline-flex items-center gap-2 ${className}`}>
      <Image
        src="/icon.png"
        alt=""
        width={28}
        height={28}
        className={`h-7 w-7 shrink-0 rounded-md object-contain ${markClassName}`}
      />
      {withWordmark && <span className="text-lg font-bold text-ink-primary">{copy.appName}</span>}
    </span>
  );
}
