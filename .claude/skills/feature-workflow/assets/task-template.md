---
id: task-XXX
title: <imperative one-liner>
repo: <repo-dir-name>   # kb-workspace mode: exactly ONE repo. single-repo mode: omit or "."
depends_on: []          # e.g. [task-001]; drives ordering + parallelism
files:                  # only what this task may create/modify, in the declared path convention
  - <path/to/file or ../<repo>/path/to/file>
model: haiku            # haiku = mechanical/bounded | sonnet = logic/ambiguity/new components
risk: low               # high = auth/payments/migrations/security/data-loss/contract change
scope: small
status: todo            # todo | in-progress | done | blocked
---

## Objective
<1–2 sentences: what to build and why.>

## Definition of Done   <!-- keep at top; each item must be concretely checkable -->
- [ ] <observable outcome 1>
- [ ] <observable outcome 2>
- [ ] <the self-check command passes>
- [ ] <covers testcases TC-x, TC-y from ./testcases.md, if applicable>

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
- Manually: <steps and expected behavior>

## Report format
Return:
1. What changed (files + short summary, or a diff).
2. The Definition of Done checklist with each item ticked or not.
3. Self-check commands run and their results.
4. If blocked (including a needed convention that isn't in this spec or SYSTEM-CONTEXT.md, or a
   write denied by a guardrail hook): where you stopped and what's missing.
