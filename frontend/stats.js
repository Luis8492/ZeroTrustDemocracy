export function computeGroupedStats(items, valueAccessor, keyAccessor) {
  const groups = new Map();
  items.forEach(item => {
    const key = keyAccessor(item);
    const value = valueAccessor(item);
    if (!groups.has(key)) {
      groups.set(key, []);
    }
    groups.get(key).push(value);
  });
  const stats = [];
  groups.forEach((values, key) => {
    const n = values.length;
    const mean = values.reduce((a, b) => a + b, 0) / n;
    const variance = n > 1
      ? values.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / (n - 1)
      : 0;
    const std = Math.sqrt(variance);
    const ci = n > 1 ? 1.96 * (std / Math.sqrt(n)) : 0;
    stats.push({ key, mean, ci, count: n });
  });
  stats.sort((a, b) => b.mean - a.mean);
  return stats;
}
