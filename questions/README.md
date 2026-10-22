# Questions

Questions are generated offline from templates, reviewed, and imported into Supabase.

```
questions/
  templates/<topic>.json   what kinds of questions exist (written by the teacher, formatted by Claude)
  batches/<name>.json      generated questions waiting for review / already imported
```

## Workflow

| Step | Who | Command |
|---|---|---|
| 1. Generate a batch from templates | Claude | → `questions/batches/<date>_<topic>_<difficulty>.json` |
| 2. Check the format | anyone | `npm run q:check` |
| 3. Run the C# snippets (.NET 10 SDK needed) | teacher's laptop | `npm run q:verify` |
| 4. Review: approve / reject | teacher | open `tools/review.html` in Edge or Chrome |
| 5. Build the SQL update | anyone | `npm run q:sql -- questions/batches/<file>.json` |
| 6. Import | teacher | paste `supabase/updates/NNN_questions_….sql` into Supabase → SQL Editor → Run |

`005_question_source_id.sql` must have been run once before the first import.
Steps 3–6 can be repeated: the verifier only re-checks changed questions, and the SQL update
matches questions by their id, so running it again updates them instead of adding duplicates.
A question set to `rejected` after an import is hidden (`is_active = false`) by the next update.

In the batch the correct answer is always **first** (easy to review). The SQL build shuffles the
answers and sets `correct_index` (the same order every time, derived from the question id), so the
API response does not give the answer away. The app shuffles them again for display.

## Batch file

```jsonc
{
  "batch": "2026-10-23_data-types_1",     // name, used in the SQL file name
  "subject": "prog-1-digi",
  "topic": "data-types",                  // = templates/<topic>.json
  "created": "2026-10-23",
  "questions": [
    {
      "id": "dt-int-arith-001",           // <template>-<NNN>, unique across ALL batches (stored as source_id)
      "template": "dt-int-arith",
      "difficulty": 2,
      "status": "pending",                // pending | approved | rejected
      "code": "int cislo = 30 / 6;",      // C# shown in the question (or null)
      "sk": {
        "body": "{code}\nAkú hodnotu bude mať premenná `cislo`?",   // {code} = where the code block goes
        "answers": ["`5`", "`36`", "`24`", "`180`"],                 // exactly 4, the CORRECT one first
        "explanation": "Najskôr sa vypočíta výraz `30 / 6` …"
      },
      "en": {
        "body": "{code}\nWhat value will the variable `cislo` have?",
        "answers": null,                  // null / missing = same as SK (code answers)
        "explanation": "First the expression `30 / 6` is evaluated …"
      },
      "verify": { "type": "value", "expr": "cislo" },
      "check": { "status": "ok", "detail": "cislo = \"5\"", "hash": "…", "at": "2026-10-23" },  // written by q:verify
      "note": "…"                         // optional, written by the review page
    }
  ]
}
```

### `verify` – how `npm run q:verify` checks a question

| type | what it does | fields |
|---|---|---|
| `output` | runs the code, stdout must equal the correct answer | `expected` (only when the answer is not inline code, e.g. `""` for *Nič*) |
| `value` | runs the code + `Console.Write(expr)`, compares with the correct answer (`"text"` / `'c'` quotes and `true`/`True` are normalised) | `expr`, optional `expected` |
| `exception` | the program must crash with this exception | `name` (e.g. `IndexOutOfRangeException`), optional `stdout` printed before the crash |
| `timeout` | the program must run forever (infinite loop) | – |
| `which-line` | each answer line is added to the code separately; only answer 1 may fail | `expect`: `compile-error`, `exception` or `timeout` (infinite loop); optional `wrap` (e.g. `"{line} { }"`), optional `lines` when answers are not inline code; `invert: true` = only answer 1 is fine (e.g. "which call is correct?") |
| `which-input` | each answer is a value put into `input` (e.g. `int x = {answer};`) before the code; only answer 1 may print `output` | `input`, `output`, optional `values`; `useCode: false` = run only the input (e.g. each answer is a whole loop) |
| `none` | concept question, nothing to run | – |

Any type may add `setup`: code put before the question's code only for checking (e.g. `int x = 4;` when the value is given in the question text).

Extra lines are inserted before the first `class` declaration, so the code may end with classes.
Programs run with invariant culture (`2.5`, not `2,5`).
