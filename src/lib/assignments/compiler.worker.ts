/// <reference lib="webworker" />
// Web Worker that hosts the .NET runtime + Roslyn (compiler/, built into public/compiler/).
// The page talks to it through runner.ts. A student's program runs here, so an endless loop
// only blocks this worker – the page terminates it after the time limit and starts a new one.
import type { WorkerRequest, WorkerResponse } from './protocol';

declare const self: DedicatedWorkerGlobalScope;

interface CheckerExports {
  Warmup(): string;
  Compile(code: string): string;
  TakeAssembly(): Uint8Array;
  Run(assembly: Uint8Array, input: string, maxOutput: number): string;
}

const FRAMEWORK = new URL(`${import.meta.env.BASE_URL}compiler/_framework/`, self.location.origin).href;
let checker: CheckerExports | null = null;

const post = (msg: WorkerResponse, transfer: Transferable[] = []) => self.postMessage(msg, transfer);

/**
 * .wasm files are deployed only as .gz – download and unpack them here. Some servers (e.g. the
 * Vite dev server) send .gz with Content-Encoding: gzip, so the browser has already unpacked it:
 * unpack only when the bytes still start with the gzip signature (1f 8b).
 */
async function fetchGz(url: string): Promise<Response> {
  const res = await fetch(url + '.gz');
  if (!res.ok) throw new Error(`${url}.gz: HTTP ${res.status}`);
  const bytes = new Uint8Array(await res.arrayBuffer());
  const headers = { 'content-type': 'application/wasm' };
  if (bytes[0] !== 0x1f || bytes[1] !== 0x8b) return new Response(bytes, { headers });
  const body = new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip'));
  return new Response(body, { headers });
}

async function init(): Promise<string> {
  const { dotnet } = await import(/* @vite-ignore */ `${FRAMEWORK}dotnet.js`);
  // When a download fails, dotnet's create() never settles – it only raises unhandled rejections.
  // Turn the first one into a failure so the page does not wait until its timeout.
  const failed = new Promise<never>((_, reject) => {
    self.addEventListener('unhandledrejection', (e) => reject(e.reason instanceof Error ? e.reason : new Error(String(e.reason))), { once: true });
  });
  const runtime = await Promise.race([failed, dotnet
    .withResourceLoader((type: string, _name: string, defaultUri: string) =>
      defaultUri.endsWith('.wasm') && (type === 'dotnetwasm' || type === 'assembly' || type === 'pdb')
        ? fetchGz(defaultUri)
        : null)
    .withConfig({ disableIntegrityCheck: true })
    .create()]);
  const config = runtime.getConfig();
  const exports = await runtime.getAssemblyExports(config.mainAssemblyName);
  checker = exports.Checker as CheckerExports;
  return checker.Warmup();
}

// NOTE: must be addEventListener – with `self.onmessage` set, dotnet's loader stalls forever
// (it then treats this worker as one of its own thread workers).
self.addEventListener('message', async (e: MessageEvent<WorkerRequest>) => {
  const msg = e.data;
  try {
    switch (msg.type) {
      case 'init': {
        const started = performance.now();
        const version = await init();
        post({ type: 'ready', version, ms: Math.round(performance.now() - started) });
        break;
      }
      case 'compile': {
        if (!checker) throw new Error('not initialised');
        const result = JSON.parse(checker.Compile(msg.code));
        const assembly = result.ok ? checker.TakeAssembly().slice() : null;
        post({ type: 'compiled', id: msg.id, result, assembly }, assembly ? [assembly.buffer] : []);
        break;
      }
      case 'run': {
        if (!checker) throw new Error('not initialised');
        const started = performance.now();
        const result = JSON.parse(checker.Run(msg.assembly, msg.input, msg.maxOutput));
        post({ type: 'ran', id: msg.id, result, ms: Math.round(performance.now() - started) });
        break;
      }
    }
  } catch (err) {
    post({ type: 'error', id: 'id' in msg ? msg.id : undefined, message: err instanceof Error ? err.message : String(err) });
  }
});
