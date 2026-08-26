# Plan — <feature name>

_Drafted: <YYYY-MM-DD> · Status: draft | awaiting-approval | executing | done | blocked_

## Summary
<what this feature is and the outcome it delivers, in 2–4 sentences.>

## Environment
<!-- Phase 0 facts — lets a later session resume execution without re-deriving them. -->
- Mode: single-repo | kb-workspace
- Host root: <absolute path — every path below is relative to this>
- Plans root: <path under the host root>
- Code paths in specs are relative to: <repo root | KB root, as `../<repo>/…`>
- Write guard: none | <unlock/lock procedure per the host contract>
- After merge (host steps): <e.g. refresh KB, rebuild relationships, record ADR | none>
- UI surface: web | mobile | none   <!-- what a task could be verified against, if asked -->
- Language: <language for everything a person reads — conversation, questions, reports,
  and the prose in these files. Template headings, enum values and commands stay English.>

## Affected repos / modules
| Repo or module | Role in this feature | Kind of change |
| --- | --- | --- |
| <name> | <producer of contract X / consumer / UI / config-only> | new / modify / config |

## Impact / ripple analysis   <!-- cross-repo/cross-module features; else delete -->
| Change | Consumers affected | Mitigation |
| --- | --- | --- |

## Execution
<!-- Set when the user approves, before the first dispatch. -->
- Mode: task-by-task | by-group | all
  <!-- How much runs between review pauses: one task · one group (a shippable slice) · everything.
       The user can change this at any pause. -->
- Progress journal + handoff: `./PROGRESS.md`
- UI tooling: not needed | <server> installed (<scope>) | user declined <server> (<date>)
  <!-- Written the first time a unit contains a `ui_verify: browser|mobile` task. Once the user
       declines a server, don't ask about it again — those tasks just return NEEDS-HUMAN. -->
- `Status:` at the top of this file follows the skill's Status discipline:
  `draft` → `awaiting-approval` → `executing` → `done` | `blocked`.

## References
- System context: `./SYSTEM-CONTEXT.md`
- Testcases (agreed BEFORE implementation): `./testcases.md`
- Task specs: `./tasks/`
- Execution trail (created at the start of execution): `./PROGRESS.md`
- Readable view of all of the above, generated — do not edit: `./dashboard.html`

## Global acceptance criteria
- [ ] <feature-level outcome 1>
- [ ] <feature-level outcome 2>

## Testcase gate
- [ ] User has reviewed and agreed to `testcases.md`. **Execution must not start before this
      box is ticked.**

## Tasks
<!-- The orchestrator reads this table to sequence and dispatch work. This table is the SOURCE
     OF TRUTH for status; each task spec's `status:` frontmatter must be kept in sync with it.
     Order producer/contract side before consumers. `group` = the slice this task belongs to
     (see § Groups): every task of a group runs before that group's integration gate is checked. -->

| id | title | repo | group | depends_on | model | risk | ui_verify | status |
|----|-------|------|-------|-----------|-------|------|-----------|--------|
| task-001 | <title> | <repo-a> | 1 | — | haiku | low | none | todo |
| task-002 | <title> | <repo-a> | 1 | task-001 | sonnet | high | none | todo |
| task-003 | <title> | <repo-b> | 2 | task-002 | haiku | low | none | todo |

`ui_verify`: `none` (default) | `browser` | `mobile`. The planner always writes `none`; only the
user turns it on, at the approval gate, for the screens they think are worth the tokens.

`status`: `todo` → `in-progress` → `done` | `blocked` | `needs-human`.
`needs-human` = code done and every command check green, but a user-visible criterion could not be
machine-verified. It does **not** block dependents; it adds a row to the queue below.

## Groups — each one is a shippable slice
<!-- A group is BOTH the unit of parallelism and the unit of reviewable, pushable work. Tasks
     inside a group have no shared files and no mutual dependency, so they run concurrently;
     when the group finishes, the feature must be in a state the user can actually push:
     no code that nothing calls, no import that nothing resolves. If a producer's only caller
     lives in the next group, the two belong in the SAME group. -->

### Group 1 — <what works end-to-end after this group>
- Tasks: task-001, task-002
- **Integration gate** (checked before reporting the group as finished):
  - [ ] Reachable: <the new code is called from <entry point> — route/screen/command/exported API
        already consumed in-repo>
  - [ ] Demonstrable: <what a person can now do, or what test now exercises the slice end-to-end>
  - [ ] No orphans: `<verbatim command that would flag dead code — lint / build / knip /
        ts-prune / vulture / the project's own check>` → exits 0
  - [ ] Pushable: the repo builds and its test suite passes with only this group's changes

### Group 2 — <…>
- Tasks: task-003
- **Integration gate**:
  - [ ] …

## Manual verification queue
<!-- One row per NEEDS-HUMAN verdict. Only the user can clear these — the orchestrator must never
     tick them off on its own. Empty is the good case. -->

| task | criterion left unverified | why the machine couldn't check it | steps to check by hand |
|---|---|---|---|
| task-00X | <what should be observable> | <no maestro / no simulator / app wouldn't start> | <the verifier's exact steps> |

## After execution / merge
- [ ] Write guard re-locked (e.g. grant file deleted), if any
- [ ] Host after-merge steps from Environment run
- [ ] Plan `Status` updated
- [ ] Manual verification queue is empty, or the user has confirmed every open row

## Notes / open questions
- <anything the user still needs to decide>
