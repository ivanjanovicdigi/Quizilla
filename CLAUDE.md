# Quizilla – notes for Claude

Mobile-first quiz app for Prog 1 students (C# / .NET 10). Repo: github.com/ivanjanovicdigi/Quizilla.
Svelte 5 + TypeScript + Vite (PWA) · Supabase Postgres (private schema `quiz`, API = RPC functions
in `public`) · deployed to GitHub Pages by GitHub Actions on push to `main`.

## Ground rules
- Explore before changing.
- **DB changes go in a NEW numbered file** in `supabase/updates/` (`0NN_name.sql`, next free number).
  Wrap in `begin; … commit;`, make it safe to re-run, CRLF line endings, header comment saying what
  it does and how to run it. The latest file that redefines a function is its current definition
  (search the updates newest-first, then `supabase/migrations/…_init.sql`).
- **Never run SQL against Supabase.** The owner runs: `npm run q:import -- supabase/updates/<file>.sql`.
- **Never suggest `npm run q:sql -- --replace-all`** – it wipes student progress.
- The owner commits and pushes. Don't commit unless asked.
- Every new UI string goes in `src/lib/i18n.svelte.ts` in both SK and EN.
- After each change: `npm run check` and `npm run build`, fix errors.
- Work one item at a time; report files changed, SQL file to import and how to test on a phone.
- Source files use CRLF line endings.

## Layout
- `src/views/` – Home, Topic, Quiz, Stats, Leaderboard, Profile, Register (login).
- `src/components/` – TopBar, BottomNav, Rich (markdown + C#), Icon, Logo, AccuracyChart,
  MedalBadge, RankBadge.
- `src/lib/api.ts` (RPC client), `types.ts`, `i18n.svelte.ts`, `util.ts` (`signed`, `pct`, …),
  `session.svelte.ts`, `router.svelte.ts` (hash router), `modes.ts` (learn/test, quiz sizes).
- `supabase/migrations/…_init.sql` – base schema; `supabase/updates/0NN_*.sql` – later changes.
- `questions/` – generators, templates and JSON batches; `scripts/` – import/check tools.
- `private/` (git-ignored) – `roster.csv`.

## Domain rules (current)
- Classes: Lambda, Ró, Teachers. Login = school email that must be in `quiz.roster` (010);
  name/class come from the roster.
- Testing mode → `submit_answer` stores into `quiz.attempts`. Learning mode → `check_answer`
  stores nothing. All stats/points/unlocks count testing answers only.
- Unlock next level: ≥ 10 answers on the level and ≥ 80 % of all of them correct (004). Sticky.
- Tiers, topic passes, ranks (009); topic medals (012).
- Scoring (013): correct +5/+10/+20 (easy/medium/hard), first correct answer of a question only
  (`points_first_correct_only`); wrong −2/−3/−5; total never below 0 – `attempts.points` stores the
  real (floored) change so totals are plain sums. `quiz.student_points(p_days)` floors period sums at 0.
  Config keys in `quiz.config`; helper `quiz.answer_points(difficulty, correct)`.
- Personal stats (014): `get_stats` per topic adds points, tier_unlocked, progress and `trend`
  (running accuracy over all answers, `[[n, correct_so_far]]`, ~60 points). UI: `Stats.svelte` +
  `TrendChart.svelte`. Students only ever see their own stats.
- Class leaderboard (015): `get_class_leaderboard()` (no args, public) – per class only the all-time
  total points, membership from active roster rows. No averages / counts / period switch.
  `get_class_ranking` (classmates' points) was dropped on purpose – don't bring it back.
- Guest mode (016): "Try as guest" on the login page. `session.guest` is memory-only; guest
  progress lives in `src/lib/guest.ts` (no localStorage, nothing on the server). RPCs
  `get_guest_catalog`, `get_guest_questions`, `check_guest_answer` take no student id and record
  nothing. Levels unlock with the student rule during the visit; tiers are all open for guests.
  Level locks for guests are enforced client-side only (server has no guest state).
- Report a bug: `src/components/BugReport.svelte` (fixed button, lower left) → Edge Function
  `supabase/functions/report-bug` (handler.ts) → public GitHub issue. Token only in Supabase secret
  `GITHUB_TOKEN`. Repo is PUBLIC → issues never contain name/email (class + first 8 chars of id).
  Quiz context comes from `src/lib/bugctx.svelte.ts` (set by Quiz.svelte). Setup: docs/BUG_REPORTS.md.
- Answer keys never leave the DB before the student answers.
