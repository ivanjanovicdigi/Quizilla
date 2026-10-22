# Quizilla load simulation

`simulate.mjs` lets N test students play **at the same time** against the real Supabase RPCs –
the same calls the app makes: login → home (`get_catalog`) → topic → questions → 10 answers
(`submit_answer`) → statistics → leaderboard. It prints the latency of every RPC and all errors.
Plain Node (no k6 or other install needed).

## Before you run it

The test accounts must exist (`test1@lyceum.sk` … `test15@lyceum.sk`, class Teachers):

```powershell
npm run q:import -- supabase/updates/023_test_accounts.sql
```

Their answers are **real** and count toward the Teachers class. Remove them afterwards:

```powershell
npm run q:import -- supabase/maintenance/delete_test_accounts.sql
```

(`023_test_accounts.sql` can be run again to recreate them for the next test.)

## Run (Windows, PowerShell, from the repo folder)

```powershell
$env:SUPABASE_URL = "https://fmsthymtbcnjmlvkztfi.supabase.co"
$env:SUPABASE_KEY = "sb_publishable_..."   # Supabase → Project Settings → API → publishable key
node loadtest/simulate.mjs                              # realistic: 15 users, 2 rounds, ~3.5 s per answer
node loadtest/simulate.mjs --users 15 --rounds 3 --think 0   # burst: no thinking, maximum pressure
```

Options: `--users N` (max = number of test accounts), `--rounds N`, `--think SECONDS` (0 = burst).
Instead of `$env:…` you can put `VITE_SUPABASE_URL` / `VITE_SUPABASE_KEY` in `.env.local`.

## How to read the result

| Column | Meaning |
|---|---|
| p50 ms | typical response time (half of the calls were faster) |
| p95 ms | slow case – 95 % of calls were faster |
| max ms | the single slowest call |
| errors | failed calls; the reason is printed below the table |

Good: 0 errors, `submit_answer` p95 well under 1 s (students feel the answer feedback).
About 60–70 ms of every call is just the network round trip to the Supabase region.

## Results – 2026-10-23 (Supabase project fmsthymtbcnjmlvkztfi)

**Realistic** – 15 users × 2 rounds, ~3.5 s thinking: 465 calls in 89 s, **0 errors**

| RPC | calls | p50 | p95 | max |
|---|---|---|---|---|
| login_student | 15 | 330 | 351 | 351 |
| get_catalog | 30 | 123 | 396 | 396 |
| get_topic | 30 | 73 | 160 | 173 |
| get_questions | 30 | 69 | 150 | 169 |
| submit_answer | 300 | 85 | 184 | 456 |
| get_stats | 30 | 131 | 917 | 934 |
| get_class_leaderboard | 30 | 67 | 169 | 206 |

**Burst** – 15 users × 3 rounds, no thinking: 690 calls in 4.3 s (**161 calls/s**), **0 errors**

| RPC | calls | p50 | p95 | max |
|---|---|---|---|---|
| login_student | 15 | 203 | 239 | 239 |
| get_catalog | 45 | 198 | 271 | 275 |
| get_topic | 45 | 82 | 112 | 125 |
| get_questions | 45 | 78 | 119 | 137 |
| submit_answer | 450 | 71 | 102 | 297 |
| get_stats | 45 | 94 | 128 | 179 |
| get_class_leaderboard | 45 | 66 | 95 | 110 |

**Conclusion:** the database handles a full class easily. A real class of 30 students answering
every ~5 s makes about 6 calls/s; the burst test ran ~160 calls/s without a single error and with
every answer back in under 0.3 s – roughly 25× headroom.

**Where it would slow down first** (only with much more data or many more users):
- `get_catalog` (Home) and `get_stats` (Statistics) are the heaviest: they recompute tiers, topic
  passes, progress and medals for every topic on every call, and that work grows with the number
  of answers a student has. The ~0.9 s `get_stats` outliers in the realistic run were the first
  calls on a cold cache.
- `login_student` is slower because it writes (creates / updates the student row) – it runs once
  per device.
- `submit_answer` locks per student (prevents double points on a double tap), so different students
  never wait for each other.
