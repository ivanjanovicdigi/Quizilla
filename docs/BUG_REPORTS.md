# "Report a bug" – setup

The small bug button (lower left corner, visible to students and guests) sends a short description
plus the current question and screen to the Supabase Edge Function **`report-bug`**
(`supabase/functions/report-bug/`). The function creates a GitHub issue in
`ivanjanovicdigi/Quizilla` with the label `bug`.

- The **GitHub token exists only as a Supabase secret** – it is never in the app or the repo.
- The repo is **public**, so issues contain **no name or email**. A student shows as
  `Lambda · student 3f9a2c1e` (first 8 characters of the student id), a guest as `Guest`.
  Find the student:
  `select name, email from quiz.students where id::text like '3f9a2c1e%';`
- The student is verified on the server (`get_student`), so a report cannot fake another class.
- Limits: description 5–2000 characters, at most 5 reports per student (guest: per IP) per 10 minutes.

## 1. GitHub token (fine-grained)

1. GitHub → **Settings → Developer settings → Personal access tokens → Fine-grained tokens →
   Generate new token** (https://github.com/settings/personal-access-tokens/new).
2. **Token name:** `quizilla-report-bug` · **Expiration:** e.g. 1 year (put a reminder to renew).
3. **Resource owner:** `ivanjanovicdigi`.
4. **Repository access:** *Only select repositories* → `Quizilla`.
5. **Permissions → Repository permissions → Issues: Read and write.**
   (Metadata: Read-only is added automatically.) Nothing else.
6. Generate and copy the token (`github_pat_…`). You will not see it again.

## 2. Secrets in Supabase

Easiest (keeps the token out of your terminal history): Supabase dashboard → your project →
**Edge Functions → Secrets** → add:

| Name | Value |
|---|---|
| `GITHUB_TOKEN` | the `github_pat_…` token |
| `ALLOWED_ORIGINS` | `https://ivanjanovicdigi.github.io,http://localhost:5173` |

Optional: `GITHUB_REPO` (default `ivanjanovicdigi/Quizilla`).
`SUPABASE_URL` and the service key are provided by Supabase automatically.

Or with the CLI (PowerShell, from the repo folder):

```powershell
npx supabase secrets set --project-ref YOUR-PROJECT-REF ALLOWED_ORIGINS=https://ivanjanovicdigi.github.io,http://localhost:5173
npx supabase secrets set --project-ref YOUR-PROJECT-REF GITHUB_TOKEN=github_pat_xxx
```

`YOUR-PROJECT-REF` = the part before `.supabase.co` in `VITE_SUPABASE_URL` (`.env.local`).

## 3. Deploy the function

From the repo folder (no install needed, `npx` downloads the Supabase CLI; no Docker needed with `--use-api`):

```powershell
npx supabase login
npx supabase functions deploy report-bug --project-ref YOUR-PROJECT-REF --no-verify-jwt --use-api
```

`--no-verify-jwt` is required: the app sends the publishable key, not a user JWT. Use the same
flags for every redeploy.

## 4. Test

In the app (phone or `npm run dev`): open a quiz question → bug button → type a description →
**Odoslať**. You get "Chyba bola nahlásená (č. N)" and issue #N appears in GitHub → Issues.

Logs: Supabase dashboard → Edge Functions → `report-bug` → Logs (GitHub errors are logged there).

## Error codes (returned to the app)

| Status | `error` | Meaning |
|---|---|---|
| 400 | `bad_request` | description too short/long, or no student/guest |
| 401 | `unknown_student` | student id not found / no longer in the roster |
| 413 | `too_large` | request over 20 kB |
| 429 | `rate_limited` | more than 5 reports in 10 minutes |
| 500 | `not_configured` | `GITHUB_TOKEN` secret missing |
| 502 | `github_error` | GitHub refused (token expired, wrong permission) – see function logs |
