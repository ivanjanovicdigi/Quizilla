# Supabase & deployment setup

About 15 minutes, done once.

## 1. Create the Supabase project

1. Sign in at <https://supabase.com> (GitHub login works) → **New project**.
2. Name: `Quizilla`, Region: **Central EU (Frankfurt)** (GDPR – students' emails are stored).
3. Generate a database password and store it in your password manager. The app never needs it.
4. Wait until the project is ready (~2 min).

## 2. Create the database

1. Left menu → **SQL Editor** → **New query**.
2. Paste the whole content of [`supabase/migrations/20261021000000_init.sql`](../supabase/migrations/20261021000000_init.sql) → **Run**.
   It should finish with "Success. No rows returned".
3. New query again → paste [`supabase/seed.sql`](../supabase/seed.sql) → **Run**.
   This adds example classes (I.A, I.B, II.A, II.B), the subject and topics. Questions are imported
   later from `supabase/updates/` (generated from `questions/templates/`).
   Run it only once.
4. Rename the example classes to your real ones, e.g.:

   ```sql
   update quiz.classes set name = '1.A' where name = 'I.A';
   insert into quiz.classes (name, sort_order) values ('3.A', 5);
   update quiz.classes set is_active = false where name = 'II.B';  -- hide a class
   ```

> The Security Advisor may list the `public.*` functions as "security definer".
> That is intentional – they are the only door into the private `quiz` schema.

## 3. Copy the API keys

**Project Settings → API Keys** (and **Data API** for the URL):

| Value | Looks like | Used as |
|---|---|---|
| Project URL | `https://abcdefgh.supabase.co` | `SUPABASE_URL` |
| Publishable key | `sb_publishable_…` (or legacy `anon` key `eyJ…`) | `SUPABASE_PUBLISHABLE_KEY` |

Both are public by design (they end up in the browser). **Never** use the `secret` / `service_role` key in the app.

Make sure **Data API** is enabled and `public` is in *Exposed schemas* (default).

## 4. GitHub Pages

In the GitHub repository:

1. **Settings → Pages → Build and deployment → Source: GitHub Actions**.
2. **Settings → Secrets and variables → Actions → Variables tab → New repository variable**:
   - `SUPABASE_URL` = Project URL
   - `SUPABASE_PUBLISHABLE_KEY` = publishable key
   - (optional) `EMAIL_DOMAIN` = `lyceum.sk` – only the hint/validation in the app; the database checks `quiz.config`.
3. **Actions → Deploy to GitHub Pages → Run workflow** (or push to `main`).
4. The app is then at `https://<user>.github.io/Quizilla/`.

## 5. Local development

```bash
cp .env.example .env.local   # fill in URL + key
npm install
npm run dev                  # open the "Network" URL on your phone (same Wi-Fi)
```

## Everyday administration (SQL Editor)

```sql
-- Reports (use "Export → CSV" in the result panel)
select * from quiz.v_student_totals;   -- per student
select * from quiz.v_student_levels;   -- per student / topic / difficulty
select * from quiz.v_class_totals;     -- class vs class

-- Roster (who may log in) – normally maintained with `npm run q:roster`, see below
select * from quiz.v_roster;                  -- roster + who has logged in
select * from quiz.v_students_not_on_roster;  -- students with progress who cannot log in

-- Move a student to another class (the roster is the source of truth; the student follows)
update quiz.roster set class_id = (select id from quiz.classes where name = 'Ró'), updated_at = now()
 where email = 'jan.novak@lyceum.sk';

-- Block a student (history is kept; the device is logged out on the next app start)
update quiz.roster set is_active = false, updated_at = now() where email = 'x@lyceum.sk';

-- Allowed email domains (comma separated)
update quiz.config set value = 'lyceum.sk' where key = 'allowed_email_domains';

-- Unlock rule per topic (defaults: 10 answers, last 10, 80 %)
update quiz.topics set unlock_min_answers = 10, unlock_window = 10, unlock_accuracy = 0.8
 where slug = 'loops';

-- Hide a question without deleting history
update quiz.questions set is_active = false where id = 42;

-- Remove a student completely (attempts are deleted too)
delete from quiz.students where email = 'x@lyceum.sk';
delete from quiz.roster   where email = 'x@lyceum.sk';
```

## Student roster (login whitelist)

Only students in `quiz.roster` can log in. They type just their school email; name and class come
from the roster, and the device remembers them (logging out is in Profile).

1. Once: `npm run q:import -- supabase/updates/010_roster.sql`
2. Export the list from Excel / EduPage as **CSV UTF-8** into `private/roster.csv`
   (the `private/` folder is gitignored – the file contains students' personal data, never commit it).
   Columns (header row, separator `;` or `,`), see [`roster.example.csv`](roster.example.csv):

   ```
   name;email;class
   Ján Novák;jan.novak@lyceum.sk;Lambda
   ```

   Columns are found by their header name, so the order does not matter (Slovak headers
   `meno;e-mail;trieda` work too). `class` must be a class name from `quiz.classes` (Lambda, Ró, Teachers).
3. Check first, then load:

   ```bash
   npm run q:roster -- private/roster.csv --dry-run
   npm run q:roster -- private/roster.csv
   ```

   Run it again whenever the list changes – new students are added, changed names/classes updated.
   Add `--sync` to also deactivate students that are no longer in the file.
   If the file has any error (bad email, unknown class, duplicate), nothing is changed.

Students who used the app before keep all their progress – they are matched by email. The script
lists existing students that are not in the roster (usually a typo in the file).

The tables are also visible in **Table Editor → schema `quiz`**.

## Free tier note

A free Supabase project is **paused after ~7 days without any traffic**. During the school year that
won't happen; after holidays open the dashboard and click **Restore**.
