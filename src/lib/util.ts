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
