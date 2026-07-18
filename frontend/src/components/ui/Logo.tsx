import Image from 'next/image';
import { copy } from '@/constants/copy';

interface LogoProps {
  withWordmark?: boolean;
  className?: string;
  markClassName?: string;
  /** Pixel size of the mark. Also sets the requested image resolution, so larger sizes stay crisp. */
  size?: number;
}

export function Logo({ withWordmark, className = '', markClassName = '', size = 28 }: LogoProps) {
  return (
    <span className={`inline-flex items-center gap-2 ${className}`}>
      <Image
        src="/icon.png"
        alt=""
        width={size}
        height={size}
        style={{ width: size, height: size }}
        className={`shrink-0 rounded-md object-contain ${markClassName}`}
      />
      {withWordmark && <span className="text-lg font-bold text-ink-primary">{copy.appName}</span>}
    </span>
  );
}
