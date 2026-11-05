#!/usr/bin/env node
// Checks coding assignments: format, then runs each reference solution (Solution.cs) with the
// .NET 10 SDK, feeds every scenario's input to the console app and compares the output with the
// expected output – with the SAME rule the browser uses (src/lib/assignments/compare.js).
// The reference solution must also match EXACTLY (case and spacing), so typos in "expected"
// are caught. Writes the result into assignment.json as "check": { status, detail, hash, at }.
//
//   npm run a:verify                       → all assignments in assignments/
//   npm run a:verify -- assignments/hotel  → only these
//   --force   re-run even when nothing changed since the last ok check
//   --keep    keep the temporary project folder (path is printed)
//   --dry     don't write results back
import { spawn } from 'node:child_process';
import { mkdirSync, writeFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, basename } from 'node:path';
import { writeJson, flag } from './lib/batch.mjs';
import { assignmentDirs, loadAssignment, validateAssignment, checkHash, linesToText } from './lib/assignments.mjs';
import { outputsMatch, firstDifference } from '../src/lib/assignments/compare.js';

const args = process.argv.slice(2);
const FORCE = flag(args, 'force');
const KEEP = flag(args, 'keep');
const DRY = flag(args, 'dry');
const DOTNET = process.env.DOTNET ?? 'dotnet';
const WORK = join(tmpdir(), 'quizilla-assignments');
const ENV = {
  ...process.env,
  DOTNET_SYSTEM_GLOBALIZATION_INVARIANT: '1',
  DOTNET_CLI_TELEMETRY_OPTOUT: '1',
  DOTNET_NOLOGO: '1',
};

function killTree(child) {
  if (child.exitCode != null) return;
  if (process.platform === 'win32') spawn('taskkill', ['/pid', String(child.pid), '/T', '/F'], { stdio: 'ignore' });
  else { try { process.kill(-child.pid, 'SIGKILL'); } catch { child.kill('SIGKILL'); } }
}

function exec(cmdArgs, cwd, { input = '', timeoutMs = 0 } = {}) {
  return new Promise((done) => {
    const child = spawn(DOTNET, cmdArgs, { cwd, env: ENV, detached: process.platform !== 'win32', windowsHide: true });
    let stdout = '';
    let stderr = '';
    let timedOut = false;
    child.stdout.setEncoding('utf8').on('data', (d) => (stdout += d));
    child.stderr.setEncoding('utf8').on('data', (d) => (stderr += d));
    child.stdin.on('error', () => {});
    child.stdin.end(input);
    const timer = timeoutMs ? setTimeout(() => { timedOut = true; killTree(child); }, timeoutMs) : null;
    child.on('error', (e) => { clearTimeout(timer); done({ code: -1, stdout, stderr: String(e), timedOut }); });
    child.on('close', (code) => {
      clearTimeout(timer);
      done({ code, stdout: stdout.replace(/\r/g, ''), stderr: stderr.replace(/\r/g, ''), timedOut });
    });
  });
}

const show = (s) => JSON.stringify(s ?? '');

async function runChecks(a) {
  const dir = join(WORK, `${a.data.slug}_${process.pid}`);
  rmSync(dir, { recursive: true, force: true });
  mkdirSync(dir, { recursive: true });
  const file = join(dir, 'Program.cs');
  writeFileSync(file, a.solution, 'utf8');
  try {
    const build = await exec(['build', file], dir, { timeoutMs: 300_000 });
    if (build.code !== 0) {
      const errs = [...new Set((build.stdout + build.stderr).split('\n').filter((l) => /error CS\d+/.test(l)).map((l) => l.replace(/^.*?(error CS\d+)/, '$1').trim()))];
      return { ok: false, detail: `Solution.cs does not compile: ${errs.join('; ') || build.stdout.trim().split('\n').slice(-3).join(' | ')}` };
    }
    const problems = [];
    for (const s of a.data.scenarios) {
      // the browser limit is per scenario; dotnet run adds process start-up, so allow 15 s here
      const r = await exec(['run', '--no-build', file], dir, { input: linesToText(s.input), timeoutMs: 15_000 });
      const expected = linesToText(s.expected);
      if (r.timedOut) { problems.push(`${s.id}: runs too long`); continue; }
      if (r.code !== 0) { problems.push(`${s.id}: exit code ${r.code} ${r.stderr.trim().split('\n')[0] ?? ''}`); continue; }
      if (!outputsMatch(r.stdout, expected)) {
        const d = firstDifference(r.stdout, expected);
        problems.push(`${s.id}: line ${d.line} is ${show(d.actual)}, expected ${show(d.expected)}`);
        continue;
      }
      const exact = r.stdout.trimEnd().split('\n').map((l) => l.trimEnd()).join('\n') === s.expected.join('\n');
      if (!exact) problems.push(`${s.id}: matches only after normalising – fix case/spacing in "expected" or Solution.cs`);
    }
    return problems.length
      ? { ok: false, detail: problems.join(' | ') }
      : { ok: true, detail: `${a.data.scenarios.length} scenarios pass` };
  } finally {
    if (KEEP) console.log(`  kept ${dir}`);
    else rmSync(dir, { recursive: true, force: true });
  }
}

const dirs = assignmentDirs(args);
if (!dirs.length) { console.error('No assignments found.'); process.exit(1); }

let failed = 0;
for (const dir of dirs) {
  const a = loadAssignment(dir);
  const name = basename(dir);
  const { errors, warnings } = validateAssignment(a);
  for (const w of warnings) console.log(`  ⚠ ${name}: ${w}`);
  if (errors.length) {
    failed++;
    console.log(`✖ ${name}: format`);
    for (const e of errors) console.log(`    - ${e}`);
    continue;
  }
  const hash = checkHash(a);
  if (!FORCE && a.data.check?.status === 'ok' && a.data.check.hash === hash) {
    console.log(`✓ ${name}: unchanged since last ok check`);
    continue;
  }
  const res = await runChecks(a);
  console.log(`${res.ok ? '✓' : '✖'} ${name}: ${res.detail}`);
  if (!res.ok) failed++;
  if (!DRY) {
    a.data.check = { status: res.ok ? 'ok' : 'fail', detail: res.detail, hash, at: new Date().toISOString().slice(0, 10) };
    writeJson(a.file, a.data);
  }
}

console.log(failed ? `\n${failed} assignment(s) need attention.` : `\nAll ${dirs.length} assignment(s) ok.`);
process.exit(failed ? 1 : 0);
