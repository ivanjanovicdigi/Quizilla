// Quizilla – "Report a bug" → GitHub issue.
// The GitHub token lives only here, as the Supabase secret GITHUB_TOKEN (never in the app).
//
// POST /functions/v1/report-bug   JSON:
//   { description: string (5–2000 chars),
//     student_id?: uuid,   – logged-in student (verified here with public.get_student)
//     guest?: true,        – guest mode
//     context: { screen, url, lang, time, app_version, quiz?: { topic_id, topic, level,
//                difficulty, mode, question_id, question, selected, answered, correct,
//                score, progress } } }
// → 201 { number, url }   errors: 400 bad_request · 401 unknown_student · 405 · 413 too_large
//                                  429 rate_limited · 500 not_configured · 502 github_error
//
// The repository is PUBLIC, so the issue never contains a name or email: a student shows as
// "<class> · student <first 8 chars of the id>" (look it up in quiz.students), a guest as "Guest".
//
// Secrets / env (Supabase → Edge Functions → Secrets):
//   GITHUB_TOKEN     required – fine-grained token, repository Quizilla, Issues: read & write
//   GITHUB_REPO      optional – default ivanjanovicdigi/Quizilla
//   ALLOWED_ORIGINS  optional – comma separated, e.g. https://ivanjanovicdigi.github.io
//   SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY / SUPABASE_ANON_KEY – provided by Supabase

type Env = { get(key: string): string | undefined };

const MAX_BODY = 20_000;
const RATE_MAX = 5; // reports per identity ...
const RATE_WINDOW = 10 * 60_000; // ... per 10 minutes (per function instance)
const recent = new Map<string, number[]>();

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

function corsHeaders(env: Env, origin: string | null): Record<string, string> {
  const allowed = (env.get('ALLOWED_ORIGINS') ?? '').split(',').map((s) => s.trim()).filter(Boolean);
  const allow = !allowed.length ? '*' : origin && allowed.includes(origin) ? origin : allowed[0];
  return {
    'Access-Control-Allow-Origin': allow,
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Access-Control-Allow-Headers': 'authorization, apikey, content-type, x-client-info',
    Vary: 'Origin'
  };
}

function json(status: number, data: unknown, cors: Record<string, string>): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: { ...cors, 'Content-Type': 'application/json' }
  });
}

/** Text for a table cell / title: one line, no pipes, no @mentions, limited length. */
function cell(v: unknown, max = 200): string {
  if (v === null || v === undefined || v === '') return '–';
  return String(v)
    .replace(/\s+/g, ' ')
    .replace(/\|/g, '\\|')
    .replace(/@/g, '@​')
    .slice(0, max);
}

/** Multi-line text inside a ~~~~ fence (cannot be closed by ``` in the text). */
function block(v: unknown, max = 4000): string {
  const s = String(v ?? '').replace(/~~~~/g, '~ ~ ~ ~').slice(0, max);
  return `~~~~text\n${s}\n~~~~`;
}

function rateLimited(key: string): boolean {
  const now = Date.now();
  const list = (recent.get(key) ?? []).filter((t) => now - t < RATE_WINDOW);
  if (list.length >= RATE_MAX) {
    recent.set(key, list);
    return true;
  }
  list.push(now);
  recent.set(key, list);
  return false;
}

async function studentLabel(env: Env, id: string): Promise<string | null> {
  const url = (env.get('SUPABASE_URL') ?? '').replace(/\/+$/, '');
  const key = env.get('SUPABASE_SERVICE_ROLE_KEY') ?? env.get('SUPABASE_ANON_KEY') ?? '';
  const headers: Record<string, string> = { 'Content-Type': 'application/json', apikey: key };
  if (key && !key.startsWith('sb_')) headers.Authorization = `Bearer ${key}`;
  const res = await fetch(`${url}/rest/v1/rpc/get_student`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ p_student_id: id })
  });
  if (!res.ok) throw new Error(`get_student ${res.status}`);
  const s = await res.json();
  if (!s) return null;
  return `${s.class_name} · student ${id.slice(0, 8)}`;
}

// deno-lint-ignore no-explicit-any
type Body = { description?: unknown; student_id?: unknown; guest?: unknown; context?: any };

export async function handle(req: Request, env: Env): Promise<Response> {
  const cors = corsHeaders(env, req.headers.get('origin'));
  if (req.method === 'OPTIONS') return new Response(null, { status: 204, headers: cors });
  if (req.method !== 'POST') return json(405, { error: 'method_not_allowed' }, cors);

  const token = env.get('GITHUB_TOKEN');
  if (!token) return json(500, { error: 'not_configured' }, cors);

  const raw = await req.text();
  if (raw.length > MAX_BODY) return json(413, { error: 'too_large' }, cors);
  let body: Body;
  try {
    body = JSON.parse(raw);
  } catch {
    return json(400, { error: 'bad_request' }, cors);
  }

  const description = typeof body.description === 'string' ? body.description.trim() : '';
  if (description.length < 5 || description.length > 2000) return json(400, { error: 'bad_request' }, cors);

  // who is reporting (verified on the server, never trusted from the app)
  let who: string;
  let rateKey: string;
  if (typeof body.student_id === 'string' && UUID.test(body.student_id)) {
    let label: string | null;
    try {
      label = await studentLabel(env, body.student_id);
    } catch (e) {
      console.error(e);
      return json(502, { error: 'server' }, cors);
    }
    if (!label) return json(401, { error: 'unknown_student' }, cors);
    who = label;
    rateKey = `s:${body.student_id}`;
  } else if (body.guest === true) {
    who = 'Guest';
    rateKey = `g:${req.headers.get('x-forwarded-for')?.split(',')[0].trim() ?? 'unknown'}`;
  } else {
    return json(400, { error: 'bad_request' }, cors);
  }
  if (rateLimited(rateKey)) return json(429, { error: 'rate_limited' }, cors);

  const ctx = body.context && typeof body.context === 'object' ? body.context : {};
  const q = ctx.quiz && typeof ctx.quiz === 'object' ? ctx.quiz : null;

  const rows: [string, unknown][] = [
    ['User', who],
    ['Screen', ctx.screen],
    ['URL', ctx.url],
    ['UI language', ctx.lang],
    ['Time (device)', ctx.time],
    ['Time (server)', new Date().toISOString()],
    ['App version', ctx.app_version]
  ];
  if (q) {
    rows.push(
      ['Question id', q.question_id],
      ['Topic', q.topic_id ? `${q.topic} (id ${q.topic_id})` : q.topic],
      ['Level / difficulty', `${q.level ?? '–'} / ${q.difficulty ?? '–'}`],
      ['Mode', q.mode],
      ['Selected answer', q.answered ? q.selected : 'not answered yet'],
      ['Result', q.answered ? (q.correct ? 'correct' : 'wrong') : '–'],
      ['Round score', q.score],
      ['Round progress', q.progress]
    );
  }

  const text = [
    '**Description**',
    '',
    description.replace(/@/g, '@​').split('\n').map((l) => `> ${l}`).join('\n'),
    '',
    '| | |',
    '|---|---|',
    ...rows.map(([k, v]) => `| ${k} | ${cell(v)} |`),
    ...(q?.question ? ['', '**Question (as shown)**', '', block(q.question)] : []),
    '',
    '_Reported from the app._'
  ].join('\n');

  const where = q?.question_id ? `Q${cell(q.question_id, 20)}` : cell(ctx.screen, 30);
  const title = `[Bug] ${where}: ${cell(description, 70)}`;

  const repo = env.get('GITHUB_REPO') ?? 'ivanjanovicdigi/Quizilla';
  const api = (env.get('GITHUB_API') ?? 'https://api.github.com').replace(/\/+$/, '');
  const gh = await fetch(`${api}/repos/${repo}/issues`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: 'application/vnd.github+json',
      'X-GitHub-Api-Version': '2022-11-28',
      'User-Agent': 'quizilla-report-bug',
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ title, body: text, labels: ['bug'] })
  });
  if (gh.status !== 201) {
    console.error('github', gh.status, await gh.text());
    return json(502, { error: 'github_error' }, cors);
  }
  const issue = await gh.json();
  return json(201, { number: issue.number, url: issue.html_url }, cors);
}
