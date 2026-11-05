// Page-side API of the in-browser C# checker. Starts the compiler worker lazily (large
// download, only when a coding assignment is opened), compiles once, then runs every scenario
// with its own time limit. A scenario that runs too long kills the worker; a fresh worker is
// started for the remaining scenarios (it reuses the compiled assembly, no second compile).
import type { CompileResult, Diagnostic, WorkerRequest, WorkerResponse } from './protocol';
import { evaluateRun, totalScore, type Scenario, type ScenarioResult } from './scoring';

export type { Diagnostic, Scenario, ScenarioResult };

export type CompilerStatus = 'idle' | 'loading' | 'ready' | 'error';

export interface CheckResult {
  compiled: boolean;
  diagnostics: Diagnostic[];
  results: ScenarioResult[];
  score: number;
  max_points: number;
}

export interface CheckProgress {
  phase: 'loading' | 'compiling' | 'running';
  scenario?: number;          // index of the scenario being run
  done?: number;
  total?: number;
}

const INIT_TIMEOUT = 180_000;   // first download on a slow school network
const COMPILE_TIMEOUT = 60_000;
const MAX_OUTPUT = 20_000;      // characters per scenario

let worker: Worker | null = null;
let ready: Promise<void> | null = null;
let nextId = 1;
let version = '';
const statusListeners = new Set<(s: CompilerStatus) => void>();
let status: CompilerStatus = 'idle';

function setStatus(s: CompilerStatus) {
  status = s;
  statusListeners.forEach((l) => l(s));
}

/** Current compiler status + subscription (returns an unsubscribe function). */
export function compilerStatus(listener?: (s: CompilerStatus) => void): { status: CompilerStatus; unsubscribe: () => void } {
  if (listener) statusListeners.add(listener);
  return { status, unsubscribe: () => listener && statusListeners.delete(listener) };
}

export const compilerVersion = () => version;

function kill() {
  worker?.terminate();
  worker = null;
  ready = null;
}

/** Waits for one reply from the worker (by id, or the ready message), with a timeout. */
function reply(w: Worker, match: (m: WorkerResponse) => boolean, timeoutMs: number): Promise<WorkerResponse | 'timeout'> {
  return new Promise((resolve) => {
    const timer = setTimeout(() => { cleanup(); resolve('timeout'); }, timeoutMs);
    const onMessage = (e: MessageEvent<WorkerResponse>) => {
      if (match(e.data)) { cleanup(); resolve(e.data); }
    };
    const onError = (e: ErrorEvent) => {
      cleanup();
      resolve({ type: 'error', message: e.message || 'worker failed' });
    };
    const cleanup = () => {
      clearTimeout(timer);
      w.removeEventListener('message', onMessage);
      w.removeEventListener('error', onError);
    };
    w.addEventListener('message', onMessage);
    w.addEventListener('error', onError);
  });
}

/** Starts the compiler (download + .NET start-up + Roslyn warm-up). Safe to call many times. */
export function loadCompiler(): Promise<void> {
  if (ready) return ready;
  setStatus('loading');
  const w = new Worker(new URL('./compiler.worker.ts', import.meta.url), { type: 'module' });
  worker = w;
  ready = (async () => {
    const pending = reply(w, (m) => m.type === 'ready' || m.type === 'error', INIT_TIMEOUT);
    w.postMessage({ type: 'init' } satisfies WorkerRequest);
    const r = await pending;
    if (r === 'timeout' || r.type !== 'ready') {
      kill();
      setStatus('error');
      throw new Error(r === 'timeout' ? 'compiler_timeout' : r.type === 'error' ? r.message : 'compiler_failed');
    }
    version = r.version;
    setStatus('ready');
  })();
  return ready;
}

async function request(msg: WorkerRequest & { id: number }, timeoutMs: number) {
  await loadCompiler();
  const w = worker!;
  const pending = reply(w, (m) => 'id' in m && m.id === msg.id, timeoutMs);
  w.postMessage(msg);
  return pending;
}

/** Compiles, then runs every scenario. Never throws for problems in the student's code. */
export async function checkCode(
  code: string,
  scenarios: Scenario[],
  timeLimitMs: number,
  onProgress?: (p: CheckProgress) => void,
): Promise<CheckResult> {
  const maxPoints = scenarios.reduce((s, x) => s + x.points, 0);
  onProgress?.({ phase: 'loading' });
  await loadCompiler();

  onProgress?.({ phase: 'compiling' });
  const c = await request({ type: 'compile', id: nextId++, code }, COMPILE_TIMEOUT);
  if (c === 'timeout') { kill(); throw new Error('compile_timeout'); }
  if (c.type === 'error') throw new Error(c.message);
  if (c.type !== 'compiled') throw new Error('unexpected_reply');
  const compile: CompileResult = c.result;
  if (!compile.ok || !c.assembly) {
    return { compiled: false, diagnostics: compile.diagnostics, results: [], score: 0, max_points: maxPoints };
  }
  const assembly = c.assembly;

  const results: ScenarioResult[] = [];
  for (const [i, s] of scenarios.entries()) {
    onProgress?.({ phase: 'running', scenario: s.index, done: i, total: scenarios.length });
    const r = await request(
      { type: 'run', id: nextId++, assembly: assembly.slice(), input: s.input, maxOutput: MAX_OUTPUT },
      timeLimitMs,
    );
    if (r === 'timeout') {
      kill(); // the program is stuck in the worker – throw the worker away
      results.push(evaluateRun(s, null, true, timeLimitMs));
      continue;
    }
    if (r.type !== 'ran') {
      // the .NET runtime itself died (e.g. endless recursion) – count it as a crash, start fresh
      kill();
      const message = r.type === 'error' ? r.message : 'unexpected reply';
      results.push(evaluateRun(s, { stdout: '', stderr: '', exception: 'RuntimeError', exception_message: message, output_limit: false }, false));
      continue;
    }
    results.push(evaluateRun(s, r.result, false, r.ms));
  }
  onProgress?.({ phase: 'running', done: scenarios.length, total: scenarios.length });

  return { compiled: true, diagnostics: compile.diagnostics, results, score: totalScore(results), max_points: maxPoints };
}
