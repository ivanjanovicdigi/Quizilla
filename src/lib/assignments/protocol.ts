// Messages between the page (runner.ts) and the compiler worker (compiler.worker.ts).

export interface Diagnostic {
  line: number;
  column: number;
  id: string;
  severity: 'error' | 'warning';
  message: string;
}

/** Something the design review points at (a class, member or statement) – line 0 = unknown. */
export interface DesignItem {
  name: string;
  line: number;
}

/** One rule of the design review (compiler/Design.cs). Texts: 'design.<id>.ok' / '.fail' in i18n. */
export interface DesignCheck {
  id: string;
  ok: boolean;
  n?: number;                  // a count the text mentions (classes, methods)
  items?: DesignItem[];        // what the rule found
}

export interface DesignClass {
  name: string;
  line: number;
  properties: number;
  fields: number;
  methods: number;
}

/** How the student's code is built. Feedback only – never part of the score. */
export interface DesignReview {
  classes: DesignClass[];
  checks: DesignCheck[];
}

export interface CompileResult {
  ok: boolean;
  diagnostics: Diagnostic[];
  design?: DesignReview;       // only when the code compiles
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
  | { type: 'analyze'; id: number; code: string }   // compile only: errors + design review, nothing is run
  | { type: 'run'; id: number; assembly: Uint8Array; input: string; maxOutput: number };

export type WorkerResponse =
  | { type: 'ready'; version: string; ms: number }
  | { type: 'compiled'; id: number; result: CompileResult; assembly: Uint8Array | null }
  | { type: 'analyzed'; id: number; result: CompileResult }
  | { type: 'ran'; id: number; result: RunResult; ms: number }
  | { type: 'error'; id?: number; message: string };
