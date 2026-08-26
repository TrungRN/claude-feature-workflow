---
id: task-XXX
title: <imperative one-liner>
repo: <repo-dir-name>   # kb-workspace mode: exactly ONE repo. single-repo mode: omit or "."
group: 1                # the shippable slice this task belongs to; must match PLAN.md § Groups
depends_on: []          # e.g. [task-001]; drives ordering + parallelism
files:                  # only what this task may create/modify, in the declared path convention
  - <path/to/file or ../<repo>/path/to/file>
model: haiku            # haiku = mechanical/bounded | sonnet = logic/ambiguity/new components
risk: low               # high = auth/payments/migrations/security/data-loss/contract change
ui_verify: none         # none (default) | browser | mobile — drive the real app to check the
                        # ### UI check block. OFF unless the user asks for it: it costs tokens.
                        # Command self-checks run either way.
scope: small
status: todo            # todo | in-progress | done | blocked | needs-human — written by the
                        # orchestrator; must always match this task's row in PLAN.md (that wins)
---

<!-- Language: prose below (Objective, DoD text, Steps…) is in the plan's recorded language.
     Headings, field names, enum values, commands and paths stay in English. -->


## Objective
<1–2 sentences: what to build and why.>

## Definition of Done   <!-- keep at top; each item must be concretely checkable.
     The boxes are ticked by the ORCHESTRATOR when the verifier returns PASS — never by the
     executor, and never in advance. Unticked boxes on a `done` task mean something went wrong. -->
- [ ] <observable outcome 1>
- [ ] <observable outcome 2>
- [ ] <the self-check command passes>
- [ ] <covers testcases TC-x, TC-y from ./testcases.md, if applicable>

## Wiring   <!-- REQUIRED whenever this task creates or exports something new.
     No task may leave code that nothing calls: state the call site explicitly. -->
- What this task adds: <function / component / endpoint / module>
- Called from: <exact file + where — the route, screen, command, or existing caller this task
  also edits — OR "task-00X in the same group, which imports it at <file>">
- After this task (plus its group), the new code is reachable from: <entry point a user or a
  test actually hits>

## Context   <!-- paste the ACTUAL current code inline; do not say "see file X" -->
```<lang>
// <path/to/file> (current, relevant excerpt)
<enough surrounding code to make the change without opening other files>
```

## Conventions this task must follow   <!-- executor has NO CLAUDE.md/KB; state them here -->
- <specific rule: styling / error handling / naming / pattern, or quote SYSTEM-CONTEXT.md § …>

## Pattern to mirror   <!-- REQUIRED when creating a new file/component; else delete -->
```<lang>
// <path/to/analogous/existing/file> — mirror this structure
<inline example>
```
Required structure: <props/params, exports, file location, naming>.

## Constraints / Do NOT touch
- <what must stay unchanged>
- <what not to add, e.g. no new dependencies>

## Expected output
<a sample diff, the shape of the result, or an example of the desired behavior>

## Self-check   <!-- verbatim commands + expected results; state the working directory -->
- In `<dir>`, run `<command>` → expected `<result>`

### UI check   <!-- Write this whenever a DoD item is user-visible, even with ui_verify: none.
     ui_verify: none    → nobody runs it automatically; it is the manual test script, and what
                          gets handed to the user if the task lands in the Manual verification queue.
     browser | mobile   → the VERIFIER drives the real app through it. Never the executor. -->
- App under test: <exact start command + URL | app id / build path + target device>
- Steps:
  1. <one deterministic action; name elements by visible label or role>
  2. <…>
- Expected: <observable result per step, tied to TC ids in ./testcases.md>

## Report format
Return:
1. What changed (files + short summary, or a diff).
2. The Definition of Done checklist with each item ticked or not.
3. Self-check commands run and their results.
4. If blocked (including a needed convention that isn't in this spec or SYSTEM-CONTEXT.md, or a
   write denied by a guardrail hook): where you stopped and what's missing.
