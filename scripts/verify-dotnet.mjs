#!/usr/bin/env node
// Verifies questions by compiling and running their C# code with the .NET 10 SDK
// (file-based apps: `dotnet build file.cs`, `dotnet run file.cs`).
// Writes the result into each question as "check": { status: "ok" | "fail", detail, hash, at }.
//
//   node scripts/verify-dotnet.mjs                     → all batches in questions/batches
//   node scripts/verify-dotnet.mjs file.json …         → only these files
//   --force        re-check questions already checked (by default only new/changed ones)
//   --id=<id>      only this question (repeatable via comma: --id=a,b)
//   --jobs=<n>     parallel runs (default 2)
//   --keep         keep the generated .cs files (printed path) for debugging
//   --dry          don't write results back into the batch files
import { spawn } from 'node:child_process';
import { mkdirSync, writeFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, basename } from 'node:path';
import { createHash } from 'node:crypto';
import { batchFiles, readJson, writeJson, flag, option, unwrapCode } from './lib/batch.mjs';

const args = process.argv.slice(2);
const FORCE = flag(args, 'force');
const KEEP = flag(args, 'keep');
const DRY = flag(args, 'dry');
const JOBS = Math.max(1, Number(option(args, 'jobs', 2)) || 2);
const ONLY = (option(args, 'id', '') || '').split(',').filter(Boolean);
const DOTNET = process.env.DOTNET ?? 'dotnet';
const WORK = join(tmpdir(), 'quizilla-verify');
const RUN_TIMEOUT = 20; // seconds for a normal run (after the build)
const LOOP_TIMEOUT = 8; // seconds after which an expected infinite loop counts as one

const ENV = {
  ...process.env,
  DOTNET_SYSTEM_GLOBALIZATION_INVARIANT: '1', // 2.5 not 2,5
  DOTNET_CLI_TELEMETRY_OPTOUT: '1',
  DOTNET_NOLOGO: '1',
};

// ------------------------------------------------------------------ process
function killTree(child) {
  if (child.exitCode != null) return;
  if (process.platform === 'win32') {
    spawn('taskkill', ['/pid', String(child.pid), '/T', '/F'], { stdio: 'ignore' });
  } else {
    try { process.kill(-child.pid, 'SIGKILL'); } catch { child.kill('SIGKILL'); }
  }
}

function exec(cmdArgs, cwd, timeoutSec) {
  return new Promise((done) => {
    const child = spawn(DOTNET, cmdArgs, { cwd, env: ENV, detached: process.platform !== 'win32', windowsHide: true });
    let stdout = '';
    let stderr = '';
    let timedOut = false;
    child.stdout.setEncoding('utf8').on('data', (d) => (stdout += d));
    child.stderr.setEncoding('utf8').on('data', (d) => (stderr += d));
    const timer = timeoutSec ? setTimeout(() => { timedOut = true; killTree(child); }, timeoutSec * 1000) : null;
    child.on('error', (e) => { clearTimeout(timer); done({ code: -1, stdout, stderr: String(e), timedOut }); });
    child.on('close', (code) => {
      clearTimeout(timer);
      done({ code, stdout: stdout.replace(/\r/g, ''), stderr: stderr.replace(/\r/g, ''), timedOut });
    });
  });
}

let seq = 0;
/** Build and (optionally) run one C# program. */
async function runProgram(source, { run = true, timeout = RUN_TIMEOUT } = {}) {
  const dir = join(WORK, `p${process.pid}_${++seq}`);
  mkdirSync(dir, { recursive: true });
  const file = join(dir, 'Program.cs');
  writeFileSync(file, source, 'utf8');
  try {
    const build = await exec(['build', file], dir, 300);
    const out = build.stdout + build.stderr;
    const errors = [...new Set(out.split('\n').filter((l) => /error CS\d+/.test(l)).map((l) => l.replace(/^.*?(error CS\d+)/, '$1').trim()))];
    if (build.code !== 0) {
      return { compiled: false, errors: errors.length ? errors : [out.trim().split('\n').slice(-5).join(' | ')], dir };
    }
    if (!run) return { compiled: true, dir };
    const r = await exec(['run', file], dir, timeout);
    const exception = /Unhandled exception\.\s*(?:System\.)?([\w.]+Exception)/.exec(r.stderr + r.stdout)?.[1] ?? null;
    return { compiled: true, ...r, exception, dir };
  } finally {
    if (!KEEP) rmSync(dir, { recursive: true, force: true });
  }
}

// ------------------------------------------------------------------ program text
const TYPE_DECL = /^\s*(?:public\s+|internal\s+)?(?:class|struct|record|enum|interface)\s+\w/m;
const PRELUDE = 'Console.OutputEncoding = System.Text.Encoding.UTF8;\n';
const MARK = '\u0001';

/** Insert statements before the first type declaration (top-level code must come first). */
function withExtra(code, extra) {
  const c = (code ?? '').replace(/\r/g, '');
  const m = TYPE_DECL.exec(c);
  const at = m ? m.index : c.length;
  return PRELUDE + c.slice(0, at).replace(/\s*$/, '\n') + extra + '\n\n' + c.slice(at);
}

// ------------------------------------------------------------------ expectations
function expectedText(q) {
  const v = q.verify;
  if (v.expected != null) return String(v.expected);
  return unwrapCode(q.sk.answers[0]);
}

function sameValue(actual, expected) {
  let e = String(expected).trim();
  const a = actual.trim();
  if (/^(true|false)$/i.test(e)) return a.toLowerCase() === e.toLowerCase();
  if (e === 'null') e = '';
  else if (/^".*"$/s.test(e)) e = e.slice(1, -1);
  else if (/^'.+'$/s.test(e)) e = e.slice(1, -1);
  return a === e;
}

const show = (s) => JSON.stringify(s.length > 80 ? s.slice(0, 80) + '…' : s);

async function verify(q) {
  const v = q.verify;
  switch (v.type) {
    case 'output': {
      const r = await runProgram(withExtra(q.code, ''));
      if (!r.compiled) return fail(`does not compile: ${r.errors.join('; ')}`);
      if (r.timedOut) return fail('runs forever (timeout)');
      if (r.exception) return fail(`crashes: ${r.exception}`);
      const exp = expectedText(q);
      return r.stdout.trimEnd() === exp.trimEnd() ? ok(`prints ${show(exp)}`) : fail(`prints ${show(r.stdout.trimEnd())}, expected ${show(exp)}`);
    }
    case 'value': {
      const r = await runProgram(withExtra(q.code, `Console.Write("${MARK}"); Console.Write(${v.expr});`));
      if (!r.compiled) return fail(`does not compile: ${r.errors.join('; ')}`);
      if (r.timedOut) return fail('runs forever (timeout)');
      if (r.exception) return fail(`crashes: ${r.exception}`);
      const value = r.stdout.includes(MARK) ? r.stdout.slice(r.stdout.lastIndexOf(MARK) + 1) : null;
      if (value == null) return fail('value was not printed');
      const exp = expectedText(q);
      return sameValue(value, exp) ? ok(`${v.expr} = ${show(value)}`) : fail(`${v.expr} = ${show(value)}, expected ${show(exp)}`);
    }
    case 'exception': {
      const r = await runProgram(withExtra(q.code, ''));
      if (!r.compiled) return fail(`does not compile: ${r.errors.join('; ')}`);
      if (r.exception !== v.name) return fail(r.exception ? `throws ${r.exception}, expected ${v.name}` : `no exception (prints ${show(r.stdout.trimEnd())})`);
      if (v.stdout != null && r.stdout.trimEnd() !== String(v.stdout)) return fail(`prints ${show(r.stdout.trimEnd())} before the crash, expected ${show(String(v.stdout))}`);
      return ok(`throws ${v.name}`);
    }
    case 'timeout': {
      const r = await runProgram(withExtra(q.code, ''), { timeout: LOOP_TIMEOUT });
      if (!r.compiled) return fail(`does not compile: ${r.errors.join('; ')}`);
      return r.timedOut ? ok('runs forever (as expected)') : fail(`ends (prints ${show(r.stdout.trimEnd())}), expected an infinite loop`);
    }
    case 'which-line': {
      const wrap = v.wrap ?? '{line}';
      const results = [];
      for (const [i, answer] of q.sk.answers.entries()) {
        const line = v.lines?.[i] ?? unwrapCode(answer);
        if (line == null) return fail(`answer ${i + 1} is not code – add verify.lines`);
        const src = withExtra(q.code, wrap.replace('{line}', line));
        const r = await runProgram(src, { run: v.expect === 'exception', timeout: RUN_TIMEOUT });
        const bad = v.expect === 'compile-error' ? !r.compiled : r.compiled && !!r.exception;
        if (v.expect === 'exception' && !r.compiled) return fail(`answer ${i + 1} does not compile: ${r.errors.join('; ')}`);
        results.push({ i, bad, why: r.errors?.join('; ') ?? r.exception });
      }
      const badOnes = results.filter((r) => r.bad).map((r) => r.i);
      const what = v.expect === 'compile-error' ? 'compile error' : 'crash';
      if (badOnes.length === 1 && badOnes[0] === 0) return ok(`only the correct answer gives a ${what} (${results[0].why})`);
      return fail(`${what} in answer(s) ${badOnes.map((i) => i + 1).join(', ') || 'none'} – expected only in answer 1`);
    }
    default:
      return null;
  }
}
const ok = (detail) => ({ status: 'ok', detail });
const fail = (detail) => ({ status: 'fail', detail });

function hashOf(q) {
  return createHash('sha1').update(JSON.stringify([q.code, q.sk.answers, q.verify])).digest('hex').slice(0, 12);
}

// ------------------------------------------------------------------ main
const probe = await exec(['--version'], process.cwd(), 30);
if (probe.code !== 0) {
  console.error(`Cannot run "${DOTNET} --version". Install the .NET 10 SDK (https://dotnet.microsoft.com/download).`);
  process.exit(2);
}
if (!/^1\d\./.test(probe.stdout.trim())) console.warn(`Warning: dotnet ${probe.stdout.trim()} – file-based apps need .NET 10 or newer.`);
mkdirSync(WORK, { recursive: true });

let okCount = 0, failCount = 0, skipCount = 0;
for (const file of batchFiles(args)) {
  const batch = readJson(file);
  const todo = batch.questions.filter((q) => {
    if (ONLY.length && !ONLY.includes(q.id)) return false;
    if (q.status === 'rejected' || !q.verify || q.verify.type === 'none') return false;
    if (!FORCE && q.check && q.check.hash === hashOf(q)) { skipCount++; return false; }
    return true;
  });
  if (!todo.length) { console.log(`${basename(file)}: nothing to check`); continue; }
  console.log(`${basename(file)}: checking ${todo.length} question(s) with ${JOBS} parallel job(s)…`);

  let next = 0;
  const worker = async () => {
    while (next < todo.length) {
      const q = todo[next++];
      let res;
      try { res = await verify(q); } catch (e) { res = fail(`checker error: ${e.message}`); }
      if (!res) continue;
      q.check = { ...res, hash: hashOf(q), at: new Date().toISOString().slice(0, 10) };
      if (res.status === 'ok') okCount++; else failCount++;
      console.log(`  ${res.status === 'ok' ? '✔' : '✖'} ${q.id}  ${res.detail}`);
    }
  };
  await Promise.all(Array.from({ length: JOBS }, worker));
  if (!DRY) writeJson(file, batch);
}

console.log(`\nok ${okCount}, failed ${failCount}, unchanged (skipped) ${skipCount}`);
process.exit(failCount ? 1 : 0);
