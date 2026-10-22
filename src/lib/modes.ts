import type { Mode } from './types';

/** Learning mode is hidden: only Play (internally mode 'test') is offered.
 *  Set to true to bring back the Learning / Play switch on the topic page. */
export const LEARNING_ENABLED = false;

/** Questions per round: learning mode is shorter and nothing is recorded. */
export const QUIZ_SIZE: Record<Mode, number> = { learn: 5, test: 10 };
