// Group items by a key, compute mean + 95% confidence interval per group.
// Falls back to the normal approximation when df > 30.

function tCriticalValue95(df: number): number {
  if (df <= 0) return 0;
  const table: Record<number, number> = {
    1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571,
    6: 2.447, 7: 2.365, 8: 2.306, 9: 2.262, 10: 2.228,
    11: 2.201, 12: 2.179, 13: 2.160, 14: 2.145, 15: 2.131,
    16: 2.120, 17: 2.110, 18: 2.101, 19: 2.093, 20: 2.086,
    21: 2.080, 22: 2.074, 23: 2.069, 24: 2.064, 25: 2.060,
    26: 2.056, 27: 2.052, 28: 2.048, 29: 2.045, 30: 2.042,
  };
  return table[df] ?? 1.96;
}

export interface GroupStat {
  key: string;
  mean: number;
  ci: number;
  count: number;
}

export function computeGroupedStats<T>(
  items: T[],
  valueAccessor: (item: T) => number | undefined,
  keyAccessor: (item: T) => string,
): GroupStat[] {
  const groups = new Map<string, number[]>();
  for (const item of items) {
    const value = valueAccessor(item);
    if (value === undefined || Number.isNaN(value)) continue;
    const key = keyAccessor(item);
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key)!.push(value);
  }
  const stats: GroupStat[] = [];
  groups.forEach((values, key) => {
    const n = values.length;
    const mean = values.reduce((a, b) => a + b, 0) / n;
    const variance =
      n > 1 ? values.reduce((sum, v) => sum + (v - mean) ** 2, 0) / (n - 1) : 0;
    const std = Math.sqrt(variance);
    const ci = n > 1 ? tCriticalValue95(n - 1) * (std / Math.sqrt(n)) : 0;
    stats.push({ key, mean, ci, count: n });
  });
  stats.sort((a, b) => b.mean - a.mean);
  return stats;
}
