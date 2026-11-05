// Line-by-line view of expected vs actual output for the feedback (same rule as compare.js:
// empty lines are ignored, case and extra whitespace do not make a line different).
import { normalizeOutput } from './compare.js';

export interface DiffRow {
  expected: string | null;   // null = the expected output has no more lines
  actual: string | null;     // null = the program printed no more lines
  same: boolean;
}

/** Non-empty lines as the student wrote them (only trailing spaces removed). */
export function visibleLines(text: string | null | undefined): string[] {
  return String(text ?? '')
    .replace(/\r\n?/g, '\n')
    .split('\n')
    .map((l) => l.replace(/\s+$/, ''))
    .filter((l) => l.trim() !== '');
}

const norm = (line: string) => normalizeOutput(line)[0] ?? '';

/** Expected and actual output side by side, aligned by line (at most `max` rows). */
export function outputDiff(actual: string, expected: string, max = 200): { rows: DiffRow[]; more: number } {
  const a = visibleLines(actual);
  const e = visibleLines(expected);
  const n = Math.max(a.length, e.length);
  const rows: DiffRow[] = [];
  for (let i = 0; i < Math.min(n, max); i++) {
    const ai = a[i] ?? null;
    const ei = e[i] ?? null;
    rows.push({ expected: ei, actual: ai, same: ai != null && ei != null && norm(ai) === norm(ei) });
  }
  return { rows, more: Math.max(0, n - max) };
}
