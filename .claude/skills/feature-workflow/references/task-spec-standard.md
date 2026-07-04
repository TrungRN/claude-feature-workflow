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
| `scope` | no | `small` / `medium` — a bound signal. |
| `status` | yes | `todo` / `in-progress` / `done` / `blocked`. Orchestrator updates. |

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
   tests), with expected results, plus any manual checks. State the working directory.
9. **Report format** — how to report back: what changed, the Definition-of-Done checklist ticked
   or not, and — if blocked — exactly where and what's missing.

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
````

## Example — BAD (and why)

> "Add validation to the signup form. Follow our patterns. Make sure it works."

Fails almost every item: no inline code, no exact paths, "follow our patterns" assumes context
the executor doesn't have, "make sure it works" isn't checkable, no self-check. A cheap model
will produce something plausible and probably wrong, in the wrong style.
