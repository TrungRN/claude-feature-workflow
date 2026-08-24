# Execution progress — <feature name>

_Plan: `<absolute path to plans/<slug>/PLAN.md>` · Host root: `<absolute path>` ·
Execution mode: `task-by-task | by-group | all` · Started: <YYYY-MM-DD>_

This file is the execution trail. It is written **as work happens**, not at the end: one journal
line per dispatch and per verdict, and the HANDOFF block at the bottom rewritten each time. If a
session dies mid-run, this file is what lets anyone — a new session, or a different AI — pick up
without guessing.

## Journal
<!-- Append-only. Never edit or delete a past line; correct with a new one. -->

| when | task | action | agent | note |
|---|---|---|---|---|
| <YYYY-MM-DD HH:MM> | task-001 | dispatch | task-executor | group 1 of 3 |
| <YYYY-MM-DD HH:MM> | task-001 | PASS | task-verifier | 2 files changed |
| <YYYY-MM-DD HH:MM> | task-002 | FAIL (1/2) | task-verifier | DoD #3 unmet: submit stays enabled on invalid email; SignupForm.tsx:61 never reads `isValid` |
| <YYYY-MM-DD HH:MM> | task-002 | dispatch (retry 1) | task-executor | verifier feedback appended |
| <YYYY-MM-DD HH:MM> | task-004 | NEEDS-HUMAN | task-verifier | commands green; UI check not run — no maestro MCP |

Actions: `dispatch` · `PASS` · `FAIL (n/2)` · `NEEDS-HUMAN` · `blocked` · `paused` (user stopped) ·
`mode-change`. For FAIL, the note must be specific enough that the next executor can fix the
problem without re-running the verifier. For NEEDS-HUMAN, name the unverified criterion and why it
couldn't be checked.

---

## HANDOFF — read this to continue
<!-- ALWAYS the last section. Overwrite it in full after every dispatch and every verdict so it
     describes the present moment. Write it for someone who has never seen this workflow. -->

**Where things stand**

- Done: <task ids + one line each, or "none yet">
- In progress / interrupted: <task id and exactly where it stopped, or "none">
- Not started: <task ids>
- Blocked: <task id + why, or "none">
- Needs human check: <task ids + what is still unverified, or "none". Code is written and its
  command checks passed; only a user-visible criterion is unconfirmed. See PLAN.md
  § Manual verification queue for the steps.>

**Files to read (absolute paths)**

- Plan and task table: `<.../plans/<slug>/PLAN.md>`
- Conventions and verbatim build/test commands: `<.../plans/<slug>/SYSTEM-CONTEXT.md>`
- Agreed testcases: `<.../plans/<slug>/testcases.md>`
- Spec for the next task: `<.../plans/<slug>/tasks/task-00X-….md>`

Code paths inside task specs are relative to: `<repo root | KB root, as ../<repo>/…>`

**Next concrete action**

<What to do next, in plain language: which task, what it must achieve, and where its Definition
of Done lives. Each task spec is self-contained — it quotes the code it touches, the conventions
to follow, and its own self-check commands. Implement exactly what the spec says, then run its
Self-check.>

**Commands** <!-- verbatim, from SYSTEM-CONTEXT.md; state the working directory -->

- In `<dir>`: `<build/typecheck command>`
- In `<dir>`: `<test command>`
- In `<dir>`: `<lint command>`
- Run the app (if the UI surface isn't `none`): in `<dir>`: `<start command>` → `<URL or device>`

**Write guard** <!-- delete if the host has none -->

<The exact unlock procedure, and the reminder to re-lock when work stops for any reason.>

**Anyone can continue from here.** This block plus the files listed above are self-contained —
you do not need this workflow's tooling, the original conversation, or any subagent. A human, or
any AI assistant with file access to the paths above, can carry on: read the next task's spec,
implement it, run its self-check, then mark it `done` in both PLAN.md's task table and the
spec's own `status:` frontmatter field, and add a line to the journal above.

Write this block in the plan's recorded language, but keep task ids, statuses, paths, and commands
verbatim in English — they are identifiers, not prose.
