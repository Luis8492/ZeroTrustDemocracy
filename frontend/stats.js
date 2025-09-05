// Return the two-sided 95% t critical value for the given degrees of freedom.
// Falls back to the normal approximation for large samples.
function tCriticalValue95(df) {
  if (df <= 0) return 0;
  const table = {
    1: 12.706,
    2: 4.303,
    3: 3.182,
    4: 2.776,
    5: 2.571,
    6: 2.447,
    7: 2.365,
    8: 2.306,
    9: 2.262,
    10: 2.228,
    11: 2.201,
    12: 2.179,
    13: 2.160,
    14: 2.145,
    15: 2.131,
    16: 2.120,
    17: 2.110,
    18: 2.101,
    19: 2.093,
    20: 2.086,
    21: 2.080,
    22: 2.074,
    23: 2.069,
    24: 2.064,
    25: 2.060,
    26: 2.056,
    27: 2.052,
    28: 2.048,
    29: 2.045,
    30: 2.042
  };
  return table[df] || 1.96;
}

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
    const ci = n > 1 ? tCriticalValue95(n - 1) * (std / Math.sqrt(n)) : 0;
    stats.push({ key, mean, ci, count: n });
  });
  stats.sort((a, b) => b.mean - a.mean);
  return stats;
}
