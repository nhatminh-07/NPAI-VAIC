export interface QuarterOption {
  value: string; // e.g. "2026-Q3"
  labelVi: string; // e.g. "Quý 3/2026"
}

// Generates the current quarter plus the `count - 1` quarters before it,
// newest first, so the period selector never goes stale.
export function recentQuarterOptions(count = 4, from = new Date()): QuarterOption[] {
  const options: QuarterOption[] = [];
  let year = from.getFullYear();
  let quarter = Math.floor(from.getMonth() / 3) + 1;

  for (let i = 0; i < count; i++) {
    options.push({ value: `${year}-Q${quarter}`, labelVi: `Quý ${quarter}/${year}` });
    quarter -= 1;
    if (quarter === 0) {
      quarter = 4;
      year -= 1;
    }
  }

  return options;
}
