// The coach: ONE next thing for the student to do, picked from everything the app knows about the
// code – compile errors, the design review (compiler/Design.cs), how the main program reads its
// commands, and the last test run. Steps follow the order a beginner builds the program in:
// write → compile → classes and their data → read the commands → link, list, methods → tests →
// clean-up. Pure logic (unit-testable); texts are 'coach.<id>.*' / 'design.<id>.*' in i18n.
import type { DesignItem, DesignReview, Diagnostic } from './protocol';
import type { Feedback } from './feedback';
import type { AssignmentScenario } from '../types';
import { normalizeOutput } from './compare.js';

/** Non-empty output lines as written (same as diff.ts; repeated so Node tests need no .ts import). */
const visibleLines = (text: string | null | undefined): string[] =>
  String(text ?? '').replace(/\r\n?/g, '\n').split('\n').map((l) => l.replace(/\s+$/, '')).filter((l) => l.trim() !== '');

/** Every step of the path, in order. Design ids are the rules of compiler/Design.cs. */
export const COACH_PATH = [
  'start', 'compile',
  'classes', 'members',
  'input_read', 'input_loop', 'input_exit',
  'link', 'storage', 'operations', 'main_state', 'instantiated', 'static',
  'tests',
  'public_fields', 'unused',
] as const;

export type CoachId = (typeof COACH_PATH)[number];

/** Steps whose texts come from the design review ('design.<id>.fail' / '.why'). */
export const DESIGN_STEPS = new Set<string>(['classes', 'members', 'link', 'storage', 'operations',
  'main_state', 'instantiated', 'static', 'public_fields', 'unused']);

/** What a test step shows: one line of expected vs actual output. */
export interface TestHint {
  index: number;
  name_sk: string;
  name_en: string;
  input: string[];
  expected: string | null;    // the expected line (null = nothing more was expected)
  actual: string | null;      // what the program printed there (null = nothing)
  line: number;               // 1-based line of the output
}

export interface CoachStep {
  id: string;                 // a COACH_PATH id, or a more exact one: 'analysing', 'run_tests', 'test_*', 'done'
  vars: Record<string, string | number>;
  items?: DesignItem[];       // places in the code (jump links)
  jump?: { line: number; column: number };
  test?: TestHint;
}

export interface Coach {
  step: CoachStep;
  done: number;               // path steps already done
  total: number;
  staleTests: boolean;        // the test result is from an older version of the code
}

export interface CoachInput {
  code: string;
  errors: Diagnostic[];             // compile errors of the code as it is now
  review: DesignReview | null;      // design review of the last version that compiled
  feedback: Feedback | null;        // last test run (fresh or stored)
  testedCode: string | null;        // the code that feedback belongs to (null = unknown)
  scenarios: AssignmentScenario[];
}

// --- how the main program reads commands (read from the source; a hint, not a proof) ----------

/** The code without comments (strings are kept – "exit" is a string). */
export function stripComments(code: string): string {
  return code.replace(/\/\*[\s\S]*?\*\/|\/\/[^\n]*/g, (m) => m.replace(/[^\n]/g, ' '));
}

const READ = /Console\s*\.\s*(ReadLine\s*\(|In\b)/g;
const LOOP_HEAD = /(\bwhile\s*\([^{}]*\)|\bfor\s*\([^{}]*\)|\bdo)\s*$/;

/** True when position `at` is inside a loop: an enclosing { } block of while/for/do, or a while ( … ) head. */
function insideLoop(c: string, at: number): boolean {
  let depth = 0;
  for (let i = at - 1; i >= 0; i--) {
    const ch = c[i];
    if (ch === '}') depth++;
    else if (ch === '{') {
      if (depth > 0) { depth--; continue; }
      if (LOOP_HEAD.test(c.slice(Math.max(0, i - 300), i))) return true;
    } else if (depth === 0 && (ch === ';')) {
      // the statement the read is in: `while ((line = Console.ReadLine()) != null)` reads in the loop head
      if (/\b(while|for)\s*\(/.test(c.slice(i + 1, at))) return true;
    }
  }
  return /\b(while|for)\s*\(/.test(c.slice(0, at).split(/[;{}]/).pop() ?? '');
}

export function programChecks(code: string): { input_read: boolean; input_loop: boolean; input_exit: boolean } {
  const c = stripComments(code);
  const reads = [...c.matchAll(READ)].map((m) => m.index ?? 0);
  return {
    input_read: reads.length > 0,
    input_loop: reads.some((at) => insideLoop(c, at)),
    input_exit: /"exit"/i.test(c),
  };
}

// --- the last test run → one concrete hint ------------------------------------------------------

const norm = (line: string) => normalizeOutput(line)[0] ?? '';

export function testHint(feedback: Feedback, scenarios: AssignmentScenario[]): CoachStep | null {
  if (!feedback.compiled) return null;
  const rows = new Map(feedback.rows.map((r) => [r.index, r]));
  for (const s of scenarios) {
    const r = rows.get(s.index);
    if (r?.passed) continue;
    const vars = { name: '' };
    const base = { index: s.index, name_sk: s.name_sk, name_en: s.name_en, input: visibleLines(s.input) };
    const expected = visibleLines(s.expected);
    const actual = visibleLines(r?.actual ?? '');
    const test = (line: number, kind: 'pair' | 'none' = 'pair'): TestHint => ({
      ...base, line: line + 1,
      expected: kind === 'pair' ? expected[line] ?? null : null,
      actual: kind === 'pair' ? actual[line] ?? null : null,
    });
    if (!r) return { id: 'run_tests', vars };
    if (r.timed_out) return { id: 'test_timeout', vars, test: test(0, 'none') };
    if (r.output_limit) return { id: 'test_output_limit', vars, test: test(0, 'none') };

    let i = 0;
    while (i < Math.max(expected.length, actual.length) && expected[i] != null && actual[i] != null && norm(expected[i]) === norm(actual[i])) i++;

    if (r.exception) {
      return { id: 'test_crash', vars: { ...vars, exception: r.exception.replace(/^System\./, ''), message: r.exception_message ?? '' }, test: test(i) };
    }
    if (actual.length === 0) return { id: 'test_silent', vars, test: test(0) };
    if (expected[i] == null) return { id: 'test_extra', vars, test: test(i) };
    if (actual[i] == null) return { id: 'test_missing', vars, test: test(i) };
    if (i === 0 && actual.slice(1).some((a) => norm(a) === norm(expected[0]))) return { id: 'test_extra_start', vars, test: test(0) };
    return { id: 'test_wrong', vars, test: test(i) };
  }
  return null;
}

// --- the coach ----------------------------------------------------------------------------------

export function buildCoach(inp: CoachInput): Coach {
  const total = COACH_PATH.length;
  const program = programChecks(inp.code);
  const checks = new Map((inp.review?.checks ?? []).map((c) => [c.id, c]));
  const staleTests = inp.feedback != null && inp.testedCode != null && inp.testedCode !== inp.code;
  const hint = inp.feedback ? testHint(inp.feedback, inp.scenarios) : null;
  const testsPassed = inp.feedback != null && inp.feedback.compiled && !staleTests && hint == null;

  const passed = (id: CoachId): boolean | null => {
    switch (id) {
      case 'start': return inp.code.trim() !== '';
      case 'compile': return inp.errors.length === 0 ? (inp.review ? true : null) : false;
      case 'input_read': case 'input_loop': case 'input_exit': return program[id];
      case 'tests': return testsPassed;
      default: return inp.review ? (checks.get(id)?.ok ?? true) : null;   // null = not known yet
    }
  };

  let done = 0;
  let step: CoachStep | null = null;
  for (const id of COACH_PATH) {
    const ok = passed(id);
    if (ok) { done++; continue; }
    if (step) continue;
    if (ok == null) { step = { id: 'analysing', vars: {} }; continue; }
    if (id === 'compile') {
      const e = inp.errors[0];
      step = { id, vars: { line: e.line, message: e.message, more: inp.errors.length - 1 }, jump: { line: e.line, column: e.column } };
    } else if (id === 'tests') {
      step = hint && inp.feedback ? hint : { id: 'run_tests', vars: {} };
      if (staleTests && !hint) step = { id: 'run_tests', vars: {} };
    } else if (DESIGN_STEPS.has(id)) {
      const c = checks.get(id);
      step = { id, vars: { n: c?.n ?? 0 }, items: c?.items };
    } else {
      step = { id, vars: {} };
    }
  }
  return { step: step ?? { id: 'done', vars: {} }, done, total, staleTests };
}

// Small generic examples for the steps that are not design rules (design examples: guide.ts).
// Code only, so they are not translated.
export const COACH_EXAMPLES: Record<string, string> = {
  input_read: `string? line = Console.ReadLine();
string[] parts = line.Split(' ');
// parts[0] is the command, parts[1], parts[2] … are its values`,
  input_loop: `while (true)
{
    string? line = Console.ReadLine();
    if (line == null) break;
    string[] parts = line.Split(' ');
    // one command per round of the loop
}`,
  input_exit: `if (parts[0] == "exit") break;`,
};
