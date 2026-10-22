#!/usr/bin/env node
// Quizilla load simulation – N test students play AT THE SAME TIME against the real RPCs,
// the same calls the app makes: login → home (get_catalog) → topic → questions → answers
// (submit_answer) → statistics → leaderboard. Then prints latency per RPC and errors.
//
//   node loadtest/simulate.mjs                       15 users, 2 rounds, 2–5 s thinking per answer
//   node loadtest/simulate.mjs --users 15 --rounds 3 --think 0     burst: no thinking, max pressure
//
// Uses the test accounts test1@lyceum.sk … testN@lyceum.sk (supabase/updates/023_test_accounts.sql).
// Their answers are REAL (they count toward the Teachers class) – remove them afterwards with
//   npm run q:import -- supabase/maintenance/delete_test_accounts.sql
//
// Needs SUPABASE_URL and SUPABASE_KEY (publishable key) – as environment variables, or
// VITE_SUPABASE_URL / VITE_SUPABASE_KEY in .env.local.
import { readFileSync, existsSync } from 'node:fs';

// ------------------------------------------------------------------ settings
const arg = (name, def) => {
  const i = process.argv.indexOf(`--${name}`);
  return i > 0 ? Number(process.argv[i + 1]) : def;
};
const USERS = arg('users', 15);
const ROUNDS = arg('rounds', 2);
const THINK = arg('think', 3.5); // average seconds between answers (±1.5 s); 0 = burst
const QUESTIONS = 10; // per round, like the app

function env(key) {
  if (process.env[key]) return process.env[key];
  if (existsSync('.env.local')) {
    for (const line of readFileSync('.env.local', 'utf8').split(/\r?\n/)) {
      const m = /^\s*([\w.]+)\s*=\s*(.*)\s*$/.exec(line);
      if (m && m[1] === key) return m[2].replace(/^["']|["']$/g, '');
    }
  }
  return '';
}
const BASE = (env('SUPABASE_URL') || env('VITE_SUPABASE_URL')).replace(/\/+$/, '');
const KEY = env('SUPABASE_KEY') || env('VITE_SUPABASE_KEY');
if (!BASE || !KEY) {
  console.error('Set SUPABASE_URL and SUPABASE_KEY (publishable key), or VITE_* in .env.local.');
  process.exit(1);
}
const headers = { 'Content-Type': 'application/json', apikey: KEY };
if (!KEY.startsWith('sb_')) headers.Authorization = `Bearer ${KEY}`;

// ------------------------------------------------------------------ measuring
const stats = new Map(); // rpc → { ms: [], errors: Map(code → n) }
function record(rpc, ms, error) {
  if (!stats.has(rpc)) stats.set(rpc, { ms: [], errors: new Map() });
  const s = stats.get(rpc);
  s.ms.push(ms);
  if (error) s.errors.set(error, (s.errors.get(error) ?? 0) + 1);
}

async function rpc(fn, args) {
  const t0 = performance.now();
  let res;
  try {
    res = await fetch(`${BASE}/rest/v1/rpc/${fn}`, { method: 'POST', headers, body: JSON.stringify(args) });
  } catch (e) {
    record(fn, performance.now() - t0, `network: ${e.cause?.code ?? e.message}`);
    return null;
  }
  const body = await res.json().catch(() => null);
  const ms = performance.now() - t0;
  if (!res.ok) {
    record(fn, ms, `${res.status} ${body?.message ?? ''}`.trim());
    return null;
  }
  record(fn, ms);
  return body;
}

const sleep = (s) => new Promise((r) => setTimeout(r, s * 1000));
const think = () => (THINK > 0 ? sleep(Math.max(0.3, THINK + (Math.random() * 3 - 1.5))) : Promise.resolve());

// ------------------------------------------------------------------ one student
async function student(n) {
  const known = new Map(); // question id → correct index (learned from earlier answers)
  const me = await rpc('login_student', { p_email: `test${n}@lyceum.sk` });
  if (!me) return;
  for (let round = 0; round < ROUNDS; round++) {
    const cat = await rpc('get_catalog', { p_student_id: me.id });
    if (!cat) return;
    // playable topics: unlocked tiers; pick one at random
    const open = new Set(cat.tiers.filter((t) => t.unlocked).map((t) => t.tier));
    const topics = cat.subjects.flatMap((s) => s.topics ?? []).filter((t) => open.has(t.tier));
    const topic = topics[Math.floor(Math.random() * topics.length)];
    if (!topic) return;
    await think();
    const tp = await rpc('get_topic', { p_student_id: me.id, p_topic_id: topic.id });
    if (!tp) return;
    const levels = tp.progress.levels.filter((l) => l.unlocked);
    const level = levels[levels.length - 1];
    const qs = await rpc('get_questions', {
      p_student_id: me.id, p_topic_id: topic.id, p_difficulty: level.difficulty, p_limit: QUESTIONS
    });
    for (const q of qs ?? []) {
      await think();
      // remembers answers seen before (repeats are right), new questions are a random guess
      const chosen = known.has(q.id) ? known.get(q.id) : Math.floor(Math.random() * 4);
      const r = await rpc('submit_answer', { p_student_id: me.id, p_question_id: q.id, p_chosen: chosen });
      if (r) known.set(q.id, r.correct_index);
    }
    await rpc('get_stats', { p_student_id: me.id, p_days: null });
    await rpc('get_class_leaderboard', {});
  }
}

// ------------------------------------------------------------------ run
const pct = (arr, p) => {
  const s = [...arr].sort((a, b) => a - b);
  return s.length ? s[Math.min(s.length - 1, Math.ceil((p / 100) * s.length) - 1)] : 0;
};

console.log(`Quizilla simulation: ${USERS} users × ${ROUNDS} rounds × ${QUESTIONS} questions, ` +
  `${THINK > 0 ? `~${THINK} s thinking per answer` : 'BURST (no thinking)'} → ${BASE}`);
const t0 = performance.now();
await Promise.all(Array.from({ length: USERS }, (_, i) => student(i + 1)));
const secs = (performance.now() - t0) / 1000;

const rows = [...stats.entries()].map(([fn, s]) => ({
  rpc: fn,
  calls: s.ms.length,
  errors: [...s.errors.values()].reduce((a, b) => a + b, 0),
  'p50 ms': Math.round(pct(s.ms, 50)),
  'p95 ms': Math.round(pct(s.ms, 95)),
  'max ms': Math.round(Math.max(...s.ms))
}));
console.table(rows);
const calls = rows.reduce((a, r) => a + r.calls, 0);
const errors = rows.reduce((a, r) => a + r.errors, 0);
console.log(`${calls} calls in ${secs.toFixed(1)} s (${(calls / secs).toFixed(1)} calls/s), ${errors} errors`);
for (const [fn, s] of stats) for (const [code, n] of s.errors) console.log(`  ${fn}: ${n}× ${code}`);
