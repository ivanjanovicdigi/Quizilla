// Output comparison for coding assignments – ONE implementation shared by the browser
// checker and the Node scripts (scripts/verify-assignments.mjs). Plain JS so Node can
// import it without a build step; types are in compare.d.ts.
//
// Rule (spec): ignore letter case and extra/trailing whitespace; everything else must match
// character by character. Concretely, for both texts:
//   * \r\n and \r become \n
//   * on every line, runs of whitespace become one space, then the line is trimmed
//   * letters are lower-cased
//   * empty lines are dropped (blank lines count as extra whitespace)
// Then the remaining lines must be equal, in the same order.

/** Normalised lines of a program output. */
export function normalizeOutput(text) {
  return String(text ?? '')
    .replace(/\r\n?/g, '\n')
    .split('\n')
    .map((line) => line.replace(/\s+/g, ' ').trim().toLowerCase())
    .filter((line) => line !== '');
}

/** True when the actual output matches the expected output under the rule above. */
export function outputsMatch(actual, expected) {
  const a = normalizeOutput(actual);
  const e = normalizeOutput(expected);
  return a.length === e.length && a.every((line, i) => line === e[i]);
}

/**
 * First line where the outputs differ (1-based, counted in the normalised lines), with both
 * normalised lines (null when one output has ended), or null when they match.
 */
export function firstDifference(actual, expected) {
  const a = normalizeOutput(actual);
  const e = normalizeOutput(expected);
  const n = Math.max(a.length, e.length);
  for (let i = 0; i < n; i++) {
    if (a[i] !== e[i]) return { line: i + 1, actual: a[i] ?? null, expected: e[i] ?? null };
  }
  return null;
}
