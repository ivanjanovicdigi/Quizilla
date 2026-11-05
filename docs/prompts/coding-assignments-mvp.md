# Quizilla – Coding Assignments MVP (Implementation Prompt)

You are working on **Quizilla** (GitHub repo `ivanjanovicdigi/Quizilla`), a lightweight quiz app for students learning C# (.NET 10). Frontend is hosted on **GitHub Pages** (static), data lives in **Supabase**. UI is switchable Slovak/English. Implement a new feature: **coding assignments**.

## Step 0 – Set up this PC first

Quizilla has never been developed on this computer. Before any feature work:

1. **Clone the repo** `https://github.com/ivanjanovicdigi/Quizilla` into the current folder (use `gh repo clone ivanjanovicdigi/Quizilla` if the GitHub CLI is installed and logged in, otherwise `git clone`). If git or GitHub auth is missing, stop and tell me what to install or log into.
2. **Get the local config from the shared folder** `Z:\Claude` (network path `\\nocniklub2\homes\nkTobias\VAR\Claude`). Copy `.env.local` from there into the repo root, and follow any setup instructions stored in that folder. Never commit `.env.local`; check it is in `.gitignore`.
3. **Check the toolchain** the repo needs (read `package.json`, the README, and any workflow files): Node/npm version, the .NET 10 SDK (needed for the in-browser compiler module), and the Supabase CLI if migrations are managed with it. Report anything missing and how to install it before continuing.
4. **Install dependencies and verify**: run the install, build, existing tests, and start the app locally against Supabase. Confirm it works before changing anything.
5. **Create a feature branch**, e.g. `feature/coding-assignments`.
6. **Save this prompt into the repository** at `docs/prompts/coding-assignments-mvp.md` and commit it on the feature branch, so the spec travels with the code to the other computer.
7. If the shared folder's setup instructions are missing or outdated, update them with what you learned (steps 1–4) so the next new machine is quicker.

## Goal

Students struggle with the basics of classes and interaction between classes. Give them small practice assignments (e.g. a hotel, library or car rental console app) where they design and write C# classes, submit the code, and get instant, detailed, test-based feedback. Main purpose is **practice**, not grading.

## Assignment template

One reusable template; Claude generates many assignments from it using different real-world domains. The teacher reviews them but does not write them. Each assignment is sized so most beginners finish within a **90-minute** assessment. Every assignment has the same scope: no bonus or optional extras.

**Hidden design (stored with the assignment, never shown to students):**

- At least **3 classes**, each with at least **2 properties**: an item class, a person class, and a manager class that ties them together.
- One-way linking (e.g. the item knows who holds it).
- The manager class has 3 operations (add, borrow/book, query).
- In-memory lists or arrays act as the database.
- About **5 test scenarios** with points totalling **100**.

**Student-facing text:** free prose, like a real client brief. It must NOT list classes, properties or methods; working out what goes where is part of the assessment. The prose DOES specify exactly the console commands and the exact output format, because tests check console I/O.

**Console I/O:** the student builds a C# console app driven by specific typed commands (e.g. `addroom 101 double`, `book 101 John john@mail.sk`, `free`), not a numbered menu. Each test scenario is a scripted input sequence plus the expected output.

**Output comparison:** ignore letter case and extra/trailing whitespace; everything else must match character by character.

**Reference example (hotel):** Room (Number, Type, IsFree, Guest), Guest (Name, Email), Hotel (Name, list of rooms; add room, book room by number for a guest, list free rooms). Scenarios: add a room 15 pts; booking a free room assigns the guest and marks it taken 25; booking a taken room fails 20; free-room list shows exactly the empty rooms 25; booking a non-existent room fails 15.

**Template format** (JSON/YAML in the repo, imported into Supabase like questions), bilingual SK/EN: title, prose brief, command and output specification, hidden reference design, scenarios (input script, expected output, points), and a reference solution used to validate the scenarios.

**Sample student brief (hotel, EN)** – use this tone for generated briefs:

> The owner of the small Hotel Tatra wants a simple console program for the reception desk. The hotel has rooms, and each room has a number and a type, like single or double. Guests stay in rooms, and the receptionist needs to know each guest's name and email.
>
> The receptionist must be able to add a new room with the command `addroom`, followed by the room number and type. The program replies `Room 101 added.`
>
> They must be able to book a room with `book`, followed by the room number, the guest's name and email. If the room is free, the program replies `Room 101 booked for John.` If it is already taken, it replies `Room 101 is not available.` If the room does not exist, it replies `Room 999 does not exist.`
>
> Finally, the command `free` lists every free room on its own line, like `101 double`, or prints `No free rooms.` if everything is taken.

**Initial assignment set:** generate one assignment per topic, in SK and EN, following the template and hotel sample: hotel, library, car rental, gym, cinema, parking garage, vet clinic, school cafeteria.

## Student flow

1. Student opens an assignment and reads the prose brief, including the command and output specification.
2. Student designs their own classes and **pastes code** into an editor area (with C# highlighting) **or uploads a .cs file**.
3. Student submits; the code is compiled and run **in the browser**, and each scenario's input script is fed to the console app.
4. Student sees detailed feedback: per scenario pass/fail, points earned, compiler errors with line numbers, and for failures the input, expected output and actual output side by side.

## Checking (in-browser)

- Compile and run the student's console app client-side using Roslyn running on WebAssembly (e.g. via a Blazor WebAssembly module or equivalent), so no backend compiler is needed. Redirect `Console.In`/`Console.Out` to feed each scenario's input script and capture the output.
- Load the compiler lazily, only when the student opens a coding assignment; show a loading indicator (it is a large download). Target is laptops/desktops (Chrome, Safari on Mac, Edge, Firefox); mobile is not a target for this feature.
- Run each scenario independently with a timeout so infinite loops do not freeze the page (e.g. run in a Web Worker).
- Accept that client-side checking can be tampered with; this is acceptable because the feature is for practice.

## Scoring and storage

- Unlimited submissions.
- **Partial points**: sum of points of passed scenarios.
- Save every submission to Supabase (user, assignment, code, per-scenario results, score, timestamp).
- The **latest submission** counts. Each assignment contributes only its latest score to the user's total, so resubmitting cannot farm points.
- Coding assignment points count **together with quiz points**: they feed personal statistics and the class leaderboard (Lambda, Rho, Teachers).
- Guests can try assignments but nothing is saved, same as guest mode for quizzes.

## Deliverables

1. DB schema/migration for assignment templates and submissions (with RLS so students see only their own submissions).
2. Template format + importer + the initial assignment set (all eight topics above), in SK and EN, each validated against its reference solution.
3. In-browser compile-and-run engine with console I/O capture, output comparison and timeouts.
4. Assignment list, assignment detail, editor/upload, and feedback UI.
5. Integration into total score, personal stats and class leaderboard.
6. Tests for the scoring and output-comparison logic, and a short README section on how to author a new assignment.

Ask before making assumptions that change the template format or the scoring rules.
