interface SpinnerProps {
  label?: string;
}

export function Spinner({ label }: SpinnerProps) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-8" role="status">
      <div className="h-10 w-10 animate-spin rounded-full border-4 border-line-grid border-t-series-1" />
      {label && <p className="text-base text-ink-secondary">{label}</p>}
    </div>
  );
}
