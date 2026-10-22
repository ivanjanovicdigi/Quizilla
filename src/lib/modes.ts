import type { Mode } from './types';

/** Questions per round: learning mode is shorter and nothing is recorded. */
export const QUIZ_SIZE: Record<Mode, number> = { learn: 5, test: 10 };
