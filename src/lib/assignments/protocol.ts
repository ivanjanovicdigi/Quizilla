// Messages between the page (runner.ts) and the compiler worker (compiler.worker.ts).

export interface Diagnostic {
  line: number;
  column: number;
  id: string;
  severity: 'error' | 'warning';
  message: string;
}

export interface CompileResult {
  ok: boolean;
  diagnostics: Diagnostic[];
}

/** One run of the student's program (as returned by Checker.Run in compiler/Checker.cs). */
export interface RunResult {
  stdout: string;
  stderr: string;
  exception?: string;          // e.g. System.NullReferenceException
  exception_message?: string;
  output_limit: boolean;       // stopped because it printed too much
  exit_code?: number;          // the program called Environment.Exit
}

export type WorkerRequest =
  | { type: 'init' }
  | { type: 'compile'; id: number; code: string }
  | { type: 'run'; id: number; assembly: Uint8Array; input: string; maxOutput: number };

export type WorkerResponse =
  | { type: 'ready'; version: string; ms: number }
  | { type: 'compiled'; id: number; result: CompileResult; assembly: Uint8Array | null }
  | { type: 'ran'; id: number; result: RunResult; ms: number }
  | { type: 'error'; id?: number; message: string };
