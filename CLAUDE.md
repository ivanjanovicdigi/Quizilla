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
  MedalBadge, RankBadge, ShareQr (Profile card with public/qr-quizilla.svg → the live app URL;
  regenerate the SVG if the app URL ever changes).
- `src/lib/api.ts` (RPC client), `types.ts`, `i18n.svelte.ts`, `util.ts` (`signed`, `pct`, …),
  `session.svelte.ts`, `router.svelte.ts` (hash router), `modes.ts` (learn/test, quiz sizes).
- `supabase/migrations/…_init.sql` – base schema; `supabase/updates/0NN_*.sql` – later changes.
- `questions/` – generators, templates and JSON batches; `scripts/` – import/check tools.
- `private/` (git-ignored) – `roster.csv`.

## Domain rules (current)
- Classes: Lambda, Ró, Teachers. Login = school email that must be in `quiz.roster` (010);
  name/class come from the roster.
- Learning mode is HIDDEN (`LEARNING_ENABLED = false` in src/lib/modes.ts); the UI calls testing
  mode "Play" / "Hrať" (internal mode name stays 'test'). Old #/quiz/…/learn links open Play.
- Testing mode → `submit_answer` stores into `quiz.attempts`. Learning mode → `check_answer`
  stores nothing. All stats/points/unlocks count testing answers only.
- Unlock next level: ≥ 20 answers on the level (019; was 10 in 004) and ≥ 80 % of all of them correct. Sticky.
- Tiers, topic passes, ranks (009); topic medals (012). Topic Grand Master (018): gold medal +
  ≥ topic_gm_accuracy (0.99) correct on EVERY level with ≥ topic_gm_min_answers (50) answers per level;
  not sticky; topic JSON medal = 'grand_master' (crown image) + `grand_master` progress object.
  Global ranks (Padawan … Grand Master over all topics) are unchanged – the user wants them as they are.
- Scoring (013, values changed in 019 – never re-run 013): correct +3/+5/+7 (easy/medium/hard),
  wrong −1/−1/−2; since 022 EVERY answer scores, repeats included
  (`points_first_correct_only` = 0; 1 = first correct answer only); total never below 0 – `attempts.points` stores the
  real (floored) change so totals are plain sums. `quiz.student_points(p_days)` floors period sums at 0.
  Config keys in `quiz.config`; helper `quiz.answer_points(difficulty, correct)`.
- Old update files are NOT safe to re-run once later files redefined their functions (009, 013).
  020 re-created get_stats after topic points showed 0 in production: 013 and 014 had never been
  applied there. 021 re-applies all scoring (013 functions + 019 values/unlock 20 + rescore) and
  prints a live/not-live row for every update 012–020 – reuse that check when something looks off.
- Personal stats are shown by `src/components/StatsPanel.svelte` – on the Stats page (Profile) and in
  the Leaderboard "Moje / Mine" tab (Leaderboard opens on "Triedy / Classes" every time).
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
- Admin (017): typing the admin phrase (no "@") on the login page → `admin_login` → session token
  (12 h) in `session.admin` → `src/views/Admin.svelte` (list roster users, activate/deactivate,
  reset progress). The phrase is NEVER in the repo (public): only a salted SHA-256 hash in
  quiz.config, set with `quiz.set_admin_passphrase()` from git-ignored `private/set_admin_passphrase.sql`.
  Admin actions are logged in quiz.admin_log.
- Test accounts (023): test1…test15@lyceum.sk in class Teachers. Remove them (with progress) via
  `supabase/maintenance/delete_test_accounts.sql` – one-off scripts that are not numbered updates live
  in supabase/maintenance/.
- Load simulation: `node loadtest/simulate.mjs` (plain Node, uses the test accounts) – see
  loadtest/README.md for how to run and the 2026-10-23 results (15 users, 0 errors).
- Answer keys never leave the DB before the student answers.
