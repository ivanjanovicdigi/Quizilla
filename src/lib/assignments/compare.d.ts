/** Normalised lines of a program output (lower-case, whitespace collapsed, no empty lines). */
export function normalizeOutput(text: string | null | undefined): string[];

/** True when the actual output matches the expected output (case and extra whitespace ignored). */
export function outputsMatch(actual: string | null | undefined, expected: string | null | undefined): boolean;

/** First differing normalised line (1-based), or null when the outputs match. */
export function firstDifference(
  actual: string | null | undefined,
  expected: string | null | undefined,
): { line: number; actual: string | null; expected: string | null } | null;
