// One display model for the feedback panel – from a fresh in-browser check or from a submission
// stored on the server (which keeps less detail: no timeouts/exceptions, errors only).
import type { CheckResult, Diagnostic } from './runner';
import type { ScenarioResult } from './scoring';
import type { CompileError, Submission } from '../types';

export interface Feedback {
  fresh: boolean;               // true = just checked in this browser
  compiled: boolean;
  diagnostics: Diagnostic[];
  rows: ScenarioResult[];
  score: number;
  max_points: number;
  submitted_at?: string;
  latest?: boolean;             // the submission that counts (vs. an older one from the history)
}

export function fromCheck(r: CheckResult): Feedback {
  return { fresh: true, compiled: r.compiled, diagnostics: r.diagnostics, rows: r.results, score: r.score, max_points: r.max_points };
}

export function fromSubmission(s: Submission, latest = true): Feedback {
  return {
    fresh: false,
    compiled: s.compiled,
    diagnostics: (s.compile_errors ?? []).map((e) => ({
      line: e.line ?? 0, column: e.column ?? 0, id: e.id ?? '', severity: 'error' as const, message: e.message,
    })),
    rows: (s.results ?? []).map((r) => ({
      index: r.scenario, passed: r.passed, points: r.points, actual: r.actual, timed_out: false, output_limit: false,
    })),
    score: s.score,
    max_points: s.max_points,
    submitted_at: s.submitted_at,
    latest,
  };
}

/** Compile errors in the shape the server stores (warnings are not sent). */
export function errorsForServer(diagnostics: Diagnostic[]): CompileError[] {
  return diagnostics
    .filter((d) => d.severity === 'error')
    .slice(0, 50)
    .map((d) => ({ line: d.line, column: d.column, id: d.id, message: d.message }));
}
