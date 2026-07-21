# Task Spec Standard

This is the format every task spec must follow, and the standard by which you judge whether a
task is ready for its executor. It is the most important file in this skill.

## Why self-contained specs matter

A strong model recovers from vague instructions by exploring and inferring. A cheap model
(Haiku) mostly can't. It fails specifically when:

- the spec says "look at X" instead of showing X,
- context — **including the project's conventions** — is assumed rather than stated,
- the task requires chaining several inferences,
- "done" is fuzzy.

So the spec must *be* the instruction. The executor should never need to open a file that isn't
quoted in the spec. This includes conventions: a dispatched executor does **not** inherit
CLAUDE.md, a knowledge base, or project memory, so any rule the task must follow has to be
written into the spec (or quoted from `SYSTEM-CONTEXT.md`, which you pass alongside it). Never
rely on the executor "already knowing the house style."

## Paths

Use the code-path convention declared in PLAN.md `## Environment` (Phase 0), consistently, in
`files`, Context headers, and prose:

- **single-repo mode**: paths relative to the repo root (`src/…`).
- **kb-workspace mode**: paths relative to the KB root (`../<repo>/…`) — the plan lives in the
  KB, the code in sibling repos.

The orchestrator tells the executor the absolute root; the executor resolves paths against it.

## Language

Prose in the spec (Objective, the text of Definition-of-Done items, Constraints, Steps) is written
in the plan's recorded language — often not English. Structure is always English: the section
headings below, every frontmatter field name and enum value, and all commands, paths, and code
identifiers. The agents match on those English headings, and the executors are cheap models that
drift when the format shifts, so translating structure breaks the pipeline while translating prose
costs nothing.

## The envelope: frontmatter + Markdown body

Use **YAML frontmatter for machine-readable metadata** (the orchestrator parses it to order,
tier, and dispatch tasks) and a **Markdown body for the executor-readable brief**. Don't bury
instructions in a giant JSON blob — models read Markdown far more reliably and inline code
survives intact. Front-load the body: the executor should learn *what it's doing* and *how
it'll know it's done* before any detail.

## Frontmatter fields

| Field | Required | Purpose |
|---|---|---|
| `id` | yes | Stable id, e.g. `task-003`. Referenced by `depends_on` and status. |
| `title` | yes | One line, imperative. |
| `repo` | kb-workspace | The single workspace repo this task edits (directory name). One repo per task — split tasks that would span two. Omit (or `.`) in single-repo mode. |
| `depends_on` | yes | Task ids that must be `done` first. `[]` if none. Drives ordering + parallelism. |
| `files` | yes | Files this task may create/modify, in the declared path convention. Keep tight. |
| `model` | yes | Execution tier: `haiku` (mechanical/bounded) or `sonnet` (logic, ambiguity, new components). |
| `risk` | yes | `high` (auth/payments/migrations/security/data-loss/contract change) or `low`. Drives verifier tier & strictness. |
| `ui_verify` | yes | Whether the verifier drives the real app: `none` (default), `browser`, or `mobile`. **The planner always writes `none`** — only the user turns it on, because driving an app costs real tokens. Command self-checks run regardless. Must match the plan's UI surface when set. |
| `scope` | no | `small` / `medium` — a bound signal. |
| `status` | yes | `todo` / `in-progress` / `done` / `blocked` / `needs-human`. Orchestrator updates. |

## Body sections (in this order)

1. **Objective** — 1–2 sentences: what to build and why.
2. **Definition of Done** — a checklist of concrete, observable outcomes, near the top. Each item
   must be checkable ("submitting an invalid email shows 'Invalid email' below the input"), not
   aspirational ("validation works"). Reference the testcases from `testcases.md` this task
   makes pass, by id, when applicable.
3. **Context** — paste the actual current code the task touches, inline, with paths, plus
   enough surrounding code to make the change without opening other files.
4. **Conventions this task must follow** — state the specific rules (styling, error component,
   naming, patterns) explicitly, or quote the exact section of `SYSTEM-CONTEXT.md`. This is the
   only convention source the executor is guaranteed to have.
5. **Pattern to mirror** *(required when creating new files/components)* — quote an analogous
   existing file inline and state the required structure: props/params, exports, file location,
   naming. New code is where a cheap model most often invents its own style.
6. **Constraints / Do NOT touch** — what must stay unchanged, what not to add (e.g. no new
   dependencies), which files are off-limits.
7. **Expected output** — a sample diff, the shape of the result, or an example of the behavior.
8. **Self-check** — the exact commands to run, **verbatim** (typecheck, lint, the specific
   tests), with expected results. State the working directory. Whenever a Definition-of-Done item
   is user-visible, add a `### UI check` subsection (below) — regardless of what `ui_verify` says.
9. **Report format** — how to report back: what changed, the Definition-of-Done checklist ticked
   or not, and — if blocked — exactly where and what's missing.

## The `### UI check` block

A command exiting 0 does not prove a screen behaves correctly. So whenever a Definition-of-Done
item is user-visible, the spec carries a script for checking it against the running app.

**Write this block whenever the task has user-visible behavior — even when `ui_verify: none`,
which is the default.** The block is worth writing either way, because who runs it depends on
`ui_verify`:

| `ui_verify` | Who runs the block |
|---|---|
| `none` *(default)* | Nobody, automatically. It is the **manual test script** — and it's what the user is handed if this task ever lands in the Manual verification queue. |
| `browser` / `mobile` | The **verifier** drives the real app through it. Never the executor. |

Writing it costs one paragraph and makes turning verification on later a one-word edit. Leaving it
out means the user has nothing to test against by hand.

Three parts, all required:

```markdown
### UI check
- App under test: <exact start command + URL, or app id / build path + which device>
- Steps:
  1. <one deterministic action per line>
  2. <…>
- Expected: <what is observable after each step, tied to TC ids from ./testcases.md>
```

- **App under test** must be runnable from what's written. `npm run dev` in `../shop-web`, then
  `http://localhost:3000/signup` — not "start the app".
- **Steps** must be unambiguous about *which* element: "click the button labelled **Sign up**",
  not "submit the form". The verifier reads the accessibility tree, so name things by their
  visible label or role.
- **Expected** must be observable, not internal: "the text `Invalid email` appears below the
  email input" — not "validation state is set".

The test of a good UI check: a stranger with no context could follow it and reach the same
verdict. If the steps only make sense to someone who already knows the feature, rewrite them.

If `ui_verify` is on but the tooling is unavailable at execution time, the verifier returns
`NEEDS-HUMAN` and
these exact steps are what the user is handed. That is another reason to write them for a human
reader.

## The Haiku-readiness checklist

Before marking a spec done, confirm every line. If any fails, fix the spec.

- [ ] Objective and Definition of Done are at the top and unambiguous.
- [ ] Every file the executor must understand is **quoted inline** — no un-pasted "see file X".
- [ ] Exact paths (in the declared convention) for everything to create or edit.
- [ ] Exactly **one concern** (no "and") — and exactly one repo, in kb-workspace mode.
- [ ] No step requires reasoning across files that aren't in the spec.
- [ ] **Conventions the task relies on are stated inline** (the executor has no CLAUDE.md).
- [ ] **New files include a "Pattern to mirror"** with an inline example and required structure.
- [ ] A concrete **example** of the expected output/behavior is present.
- [ ] A **runnable self-check** with verbatim commands, expected results, and working directory.
- [ ] Constraints say what NOT to touch.
- [ ] `model` and `risk` are set appropriately for the task's difficulty and blast radius.
- [ ] `ui_verify` is `none` unless the user explicitly asked to turn it on for this task.
- [ ] If any Definition-of-Done item is user-visible, a `### UI check` block exists and is complete
      enough for a stranger to run — with `ui_verify: none` that stranger is the user.
- [ ] Small enough to fit comfortably in one executor context.

## Example — GOOD (excerpt, kb-workspace mode)

````markdown
## Definition of Done
- [ ] Entering an invalid email (e.g. "abc") and blurring shows "Invalid email" below the input.
- [ ] Submit is disabled while the email is empty or invalid.
- [ ] A valid email clears the error and re-enables Submit.
- [ ] `npm run typecheck` (in `../shop-web`) passes.
- [ ] Covers testcases TC-3 and TC-4 in ./testcases.md.

## Context
```tsx
// ../shop-web/src/components/SignupForm.tsx (current, relevant excerpt)
const [email, setEmail] = useState("");
// ... enough surrounding code to make the edit without opening other files
```

## Conventions this task must follow
- Inline errors use the existing `<FieldError message={...} />` from `@/components/FieldError`.
- Styling is Tailwind; error text uses `text-sm text-red-600` (see SYSTEM-CONTEXT.md § shop-web
  › Styling).

## Constraints / Do NOT touch
- Do not modify the submit network call beyond gating it on validity.
- Do not add a validation library (no yup/zod); a regex is fine.

## Self-check
- In `../shop-web`, run `npm run typecheck` → exits 0, no errors.

### UI check
- App under test: in `../shop-web`, `npm run dev` → http://localhost:3000/signup
- Steps:
  1. Type `abc` into the field labelled **Email**.
  2. Click the field labelled **Password** so Email loses focus.
  3. Clear Email and type `a@b.com`.
- Expected: after step 2, the text `Invalid email` appears below the Email input and the
  **Sign up** button is disabled (TC-3). After step 3, the error text is gone and **Sign up**
  is enabled (TC-4).
````

## Example — BAD (and why)

> "Add validation to the signup form. Follow our patterns. Make sure it works."

Fails almost every item: no inline code, no exact paths, "follow our patterns" assumes context
the executor doesn't have, "make sure it works" isn't checkable, no self-check. A cheap model
will produce something plausible and probably wrong, in the wrong style.
