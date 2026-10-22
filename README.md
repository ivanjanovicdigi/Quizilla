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
- **Points:** `difficulty × 10` for the **first** correct answer of each question
  (repeating known questions gives practice, not points).
- **Class leaderboard:** average points per registered student (fair for different class sizes),
  last 7 days or all time. Inside a class, classmates are shown as "Ján N.".
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
