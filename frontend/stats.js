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
    const mean = values.reduce((a, b) => a + b, 0) / values.length;
    const variance = values.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / values.length;
    const std = Math.sqrt(variance);
    stats.push({ key, mean, std, count: values.length });
  });
  stats.sort((a, b) => b.mean - a.mean);
  return stats;
}
