// Pure scoring logic for coding assignments (no browser APIs – unit-testable).
// The server recomputes the score from its own scenario points (030 submit_assignment);
// this is what the student sees immediately.
import { outputsMatch } from './compare.js';
import type { RunResult } from './protocol';

export interface Scenario {
  index: number;
  name_sk: string;
  name_en: string;
  input: string;
  expected: string;
  points: number;
}

export interface ScenarioResult {
  index: number;
  passed: boolean;
  points: number;             // earned: scenario points if passed, else 0
  actual: string;             // what the program printed
  timed_out: boolean;
  output_limit: boolean;
  exception?: string;         // crashed with this exception (output is still compared)
  exception_message?: string;
  exit_code?: number;
  ms?: number;
}

/** Pass/fail of one scenario. A timeout or too much output fails; a crash fails only if the output is wrong. */
export function evaluateRun(scenario: Scenario, run: RunResult | null, timedOut: boolean, ms?: number): ScenarioResult {
  const actual = run?.stdout ?? '';
  const outputLimit = run?.output_limit ?? false;
  const passed = !timedOut && !outputLimit && run != null && outputsMatch(actual, scenario.expected);
  return {
    index: scenario.index,
    passed,
    points: passed ? scenario.points : 0,
    actual,
    timed_out: timedOut,
    output_limit: outputLimit,
    exception: run?.exception,
    exception_message: run?.exception_message,
    exit_code: run?.exit_code,
    ms,
  };
}

/** Sum of the points of passed scenarios (each scenario counted once). */
export function totalScore(results: Pick<ScenarioResult, 'index' | 'passed' | 'points'>[]): number {
  const seen = new Set<number>();
  let sum = 0;
  for (const r of results) {
    if (!r.passed || seen.has(r.index)) continue;
    seen.add(r.index);
    sum += r.points;
  }
  return sum;
}
