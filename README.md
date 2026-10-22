# Quizilla

Lightweight, mobile-first quiz app for students to practise basic knowledge.
Subjects → topics → questions with difficulty levels; higher levels unlock after
reaching a threshold on the current one; students compete class vs class.
UI in Slovak and English; C# code is formatted and highlighted.

**Setup guide:** [docs/SUPABASE_SETUP.md](docs/SUPABASE_SETUP.md)

## Stack

| Part | Technology |
|---|---|
| App | Svelte 5 + TypeScript + Vite, installable PWA (works offline for the shell) |
| C# highlighting | Prism (`prism-csharp`), tiny safe Markdown subset |
| Backend | Supabase Postgres – private `quiz` schema + `public.*` RPC functions |
| Hosting | GitHub Pages via GitHub Actions |

Production bundle ≈ 40 kB gzipped JS + 4 kB CSS.

## How it works

- **Identity (MVP):** student enters name, school email (`@lyceum.sk`, checked in the DB) and class.
  The app stores the returned student id on the device. Re-entering the same email on another
  device logs back into the same profile. Class can only be changed by the teacher.
  *No password – a student could type a classmate's email. Upgrade path: Supabase email OTP.*
- **Levels** are derived from the distinct `difficulty` values of a topic's active questions
  (e.g. 1, 2, 3 → levels 1–3). Add questions with a new difficulty and a new level appears.
- **Unlock rule** (per topic, configurable): at least `unlock_min_answers` answers on the
  current level **and** ≥ `unlock_accuracy` correct in the last `unlock_window` answers.
  Unlocks are sticky. The server refuses questions/answers for locked levels.
- **Points (testing mode only):** correct answer easy +5, medium +10, hard +20 – only the
  **first** correct answer of each question scores (repeats give 0). Wrong answer easy −2,
  medium −3, hard −5. A student's total never goes below 0 (a penalty is cut to the current
  total). Values are in `quiz.config` (`points_correct_1..3`, `points_wrong_1..3`,
  `points_first_correct_only`).
- **Guest mode:** "Try as guest" on the login page – no roster needed, nothing is saved (no
  attempts, points or leaderboard). Levels unlock during the visit only; a reload starts from zero.
- **Report a bug:** small button in the lower left corner → GitHub issue via the Supabase Edge
  Function `report-bug` (token stays on the server). Setup: [docs/BUG_REPORTS.md](docs/BUG_REPORTS.md).
- **Class leaderboard:** visible to everyone – one column per class (Lambda, Ró, Teachers) with the
  class total: plain sum of all-time points of its roster students. Students see only their own
  detailed statistics, never classmates' points.
- **Answer keys never leave the database** before the student answers.

## Project structure

```
src/
  App.svelte            routes (hash router) + session check
  views/                Register, Home, Topic, Quiz, Leaderboard, Profile
  components/           TopBar, BottomNav, Rich (markdown + C#), Icon, Logo
  lib/api.ts            RPC client (fetch → /rest/v1/rpc/*)
  lib/i18n.svelte.ts    SK/EN texts
  lib/rich.ts           Markdown subset + Prism
supabase/
  migrations/…_init.sql schema, RPC functions, teacher views
  seed.sql              sample classes, subject and topics (no questions)
  tests/api_test.sql    SQL smoke test (run as superuser on a test DB)
```

## Question format (`quiz.questions`)

| Column | Notes |
|---|---|
| `topic_id`, `difficulty` | difficulty 1–10 |
| `body` | Markdown subset: paragraphs, `**bold**`, `` `inline` ``, fenced ```` ```csharp ```` blocks |
| `answers` | `text[]` with exactly 4 items (same Markdown subset; the app shuffles them) |
| `correct_index` | 0–3 |
| `explanation` | optional, shown after answering |
| `body_en`, `answers_en`, `explanation_en` | optional English versions; shown when the UI is in English, otherwise the Slovak columns are used |

Bulk import is a separate task (planned).

## Development

```bash
npm install
cp .env.example .env.local   # Supabase URL + publishable key
npm run dev                  # http://localhost:5173 (+ network URL for phone)
npm run check                # type check
npm run build                # production build into dist/
```

Testing against a local Postgres + PostgREST instead of Supabase:
`LOCAL_API=http://localhost:3000 npm run dev` (leave `VITE_SUPABASE_URL` empty).
