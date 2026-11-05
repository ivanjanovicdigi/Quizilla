# Coding assignments

Small C# console apps (hotel, library, …) that students design and write themselves. The app
compiles and runs the student's code in the browser, feeds each test scenario as console input and
compares the output. Spec: [docs/prompts/coding-assignments-mvp.md](../docs/prompts/coding-assignments-mvp.md).

```
assignments/<slug>/
  assignment.json   briefs (SK/EN), hidden design, scenarios, status, check result
  Solution.cs       hidden reference solution – proves the scenarios are right
```

## Workflow

| Step | Who | Command |
|---|---|---|
| 1. Write / generate an assignment from the template below | Claude | `assignments/<slug>/` |
| 2. Check format + run the reference solution (.NET 10 SDK) | anyone | `npm run a:verify` |
| 3. Review the brief and scenarios, set `"status": "approved"` | teacher | edit `assignment.json` |
| 4. Build the SQL update | anyone | `npm run a:sql` (add `--include-pending` to show pending ones too) |
| 5. Import | teacher | `npm run q:import -- supabase/updates/NNN_assignments_….sql` |

`030_coding_assignments.sql` must be imported once first. Re-running steps 2–5 is safe: the verifier
only re-runs changed assignments, and the SQL matches assignments by `slug`. `a:sql` refuses
assignments that were changed after their last successful check.

Who sees assignments at all is set in the database, not here:
`quiz.config 'assignments_access'` = comma-separated emails, or `*` for everyone (guests included).

## The template (same scope for every assignment)

- Sized for a **90-minute** assessment for beginners. No bonus or optional parts.
- **Hidden design:** ≥ 3 classes with ≥ 2 properties each – an **item**, a **person** and a
  **manager** that ties them together; a **one-way link** (the item knows its person); the manager has
  **3 operations**: add, assign (book/borrow/rent…), query; in-memory `List<T>` as the database.
- **5 scenarios, 100 points:** add 15 · assign a free item 25 · assign a taken item fails 20 ·
  query is exact 25 · assign a missing item fails 15.
- **Brief:** free prose like a real client. It never names classes, properties or methods, but it
  states every command and every reply exactly. Commands and replies are **English in both
  languages**; only the prose is translated. The last paragraph is always the standard rules:
  one command per line, `exit` ends the program, every value is one word, nothing else is printed.
- Lists are printed in the order items were added.

## `assignment.json`

```jsonc
{
  "slug": "hotel",                 // = folder name; a-z, 0-9, dashes
  "sort_order": 10,                // order in the app
  "status": "pending",             // pending | approved | rejected
  "max_points": 100,               // scenario points must add up to this
  "time_limit_ms": 3000,           // per scenario in the browser
  "sk": { "title": "Hotel Tatra", "brief": ["paragraph", "…"] },   // Markdown subset, `code`
  "en": { "title": "Hotel Tatra", "brief": ["paragraph", "…"] },
  "design": {                      // hidden; never sent to the app
    "classes": [
      { "name": "Room", "role": "item", "properties": ["int Number", "string Type", "Guest? Guest"] },
      { "name": "Guest", "role": "person", "properties": ["string Name", "string Email"] },
      { "name": "Hotel", "role": "manager", "properties": ["string Name", "List<Room> Rooms"],
        "operations": ["AddRoom(number, type)", "Book(number, guest)", "FreeRooms()"] }
    ],
    "link": "Room.Guest → Guest",
    "storage": "List<Room> in Hotel"
  },
  "scenarios": [
    {
      "id": "add-room",            // unique in the assignment
      "sk": "Pridanie izby", "en": "Adding a room",   // shown in the feedback
      "points": 15,
      "input": ["addroom 101 double", "exit"],        // lines typed into the console; must end with exit
      "expected": ["Room 101 added."]                 // exact lines the program prints
    }
  ],
  "check": { "status": "ok", "detail": "5 scenarios pass", "hash": "…", "at": "2026-11-05" }  // written by a:verify
}
```

## How output is compared

`src/lib/assignments/compare.js` – the same code in the browser and in `a:verify`:
letter case is ignored, runs of spaces/tabs count as one space, spaces at line ends and empty
lines are ignored; everything else must match character by character. The verifier is stricter
for the reference solution (exact case and spacing), so typos in `expected` are caught.

`a:verify` checks the format (points add up, every command appears in both briefs as `` `cmd` ``,
inputs end with `exit`, design has item/person/manager…), then runs `Solution.cs` once per scenario.
