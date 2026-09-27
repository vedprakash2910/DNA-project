// src/utils/chartData.js
//
// Chart data-transformation layer.
//
// analyzeSequences() (in api/dnaApi.js) gives us a flat array of mutation
// objects: { type, position, original, mutated }. That shape is convenient
// for a table row but not for a chart — Recharts wants pre-aggregated
// series data. These helpers do that conversion in one place so the table,
// the distribution chart, and the position chart all read from the same
// source of truth instead of three separate ad-hoc reductions.

export const MUTATION_TYPES = ["Substitution", "Insertion", "Deletion"];

// Same palette already used for the mutation-type pills in the results
// table (see .mutation-type--* in App.css), reused here so the charts and
// the table stay visually consistent.
export const TYPE_COLORS = {
  Substitution: "#88ff3d",
  Insertion: "#5eeada",
  Deletion: "#a788fa",
};

/**
 * Counts mutations per type, for the "Mutation Type Distribution" chart.
 * Always returns all three types (even at count 0) so the bar/pie chart's
 * shape stays stable as the user switches filters, instead of a type
 * disappearing entirely the moment its count hits zero.
 *
 * @param {Array<{type: string}>} mutations
 * @returns {Array<{type: string, count: number, percentage: number, fill: string}>}
 */
export function getTypeDistribution(mutations) {
  const counts = { Substitution: 0, Insertion: 0, Deletion: 0 };

  for (const mutation of mutations) {
    if (mutation && Object.prototype.hasOwnProperty.call(counts, mutation.type)) {
      counts[mutation.type] += 1;
    }
  }

  const total = mutations.length;

  return MUTATION_TYPES.map((type) => ({
    type,
    count: counts[type],
    // Rounded to 1 decimal place — plenty of precision for a chart label.
    percentage: total === 0 ? 0 : Math.round((counts[type] / total) * 1000) / 10,
    fill: TYPE_COLORS[type],
  }));
}

// Fixed row per type on the scatter chart's y-axis, so mutations of
// different types land on separate horizontal bands instead of stacking
// on top of one another at the same y value.
const TYPE_ROW = { Deletion: 0, Insertion: 1, Substitution: 2 };

/**
 * One point per mutation: { position, y, type, original, mutated }.
 * Feeds the scatter view of the "Mutation Position Map" chart. Points with
 * a non-numeric/invalid position are dropped rather than plotted at 0,
 * since that would misrepresent where the mutation actually is.
 *
 * @param {Array<{type: string, position: number, original: string, mutated: string}>} mutations
 */
export function getScatterData(mutations) {
  return mutations
    .filter((m) => m && Number.isFinite(m.position))
    .map((m) => ({
      position: m.position,
      y: TYPE_ROW[m.type] ?? 1,
      type: m.type,
      original: m.original,
      mutated: m.mutated,
    }));
}

/**
 * Groups mutations into equal-width position bins across the sequence, for
 * the line view of the "Mutation Position Map" chart. A raw one-bar/point
 * per base-pair position would be unreadable for anything beyond a very
 * short sequence, so this reduces the x-axis to a fixed number of buckets
 * (default 20) and counts mutations per bucket — showing where mutations
 * cluster along the sequence rather than every individual position.
 *
 * @param {Array<{position: number}>} mutations
 * @param {number} binCount
 * @returns {Array<{binStart: number, binEnd: number, count: number, label: string}>}
 */
export function getPositionDensity(mutations, binCount = 20) {
  const positions = mutations
    .filter((m) => m && Number.isFinite(m.position))
    .map((m) => m.position);

  if (positions.length === 0) return [];

  const minPosition = Math.min(...positions);
  const maxPosition = Math.max(...positions);
  const span = Math.max(1, maxPosition - minPosition + 1);
  const binSize = Math.max(1, Math.ceil(span / binCount));

  const bins = new Map();

  for (const position of positions) {
    const binStart = minPosition + Math.floor((position - minPosition) / binSize) * binSize;

    if (!bins.has(binStart)) {
      bins.set(binStart, {
        binStart,
        binEnd: binStart + binSize - 1,
        count: 0,
      });
    }
    bins.get(binStart).count += 1;
  }

  return Array.from(bins.values())
    .sort((a, b) => a.binStart - b.binStart)
    .map((bin) => ({
      ...bin,
      label: bin.binStart === bin.binEnd ? `${bin.binStart}` : `${bin.binStart}-${bin.binEnd}`,
    }));
}
