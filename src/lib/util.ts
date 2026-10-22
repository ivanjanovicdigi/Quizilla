/** Fisher–Yates shuffle of [0..n-1]. */
export function shuffledIndices(n: number): number[] {
  const a = Array.from({ length: n }, (_, i) => i);
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

/** Correct answers needed in the window to meet the threshold. */
export function neededCorrect(window: number, accuracy: number): number {
  return Math.ceil(window * accuracy - 1e-9);
}

/** Success rate in whole %, rounded down (79.9 % shows as 79 – not yet 80 %). */
export function pct(correct: number, total: number): number {
  return total ? Math.floor((correct * 100) / total) : 0;
}
