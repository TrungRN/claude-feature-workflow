# Plan — <feature name>

_Drafted: <YYYY-MM-DD> · Status: draft | awaiting-approval | executing | done | blocked_

## Summary
<what this feature is and the outcome it delivers, in 2–4 sentences.>

## Environment
<!-- Phase 0 facts — lets a later session resume execution without re-deriving them. -->
- Mode: single-repo | kb-workspace
- Plans root: <path>
- Code paths in specs are relative to: <repo root | KB root, as `../<repo>/…`>
- Write guard: none | <unlock/lock procedure per the host contract>
- After merge (host steps): <e.g. refresh KB, rebuild relationships, record ADR | none>

## Affected repos / modules
| Repo or module | Role in this feature | Kind of change |
| --- | --- | --- |
| <name> | <producer of contract X / consumer / UI / config-only> | new / modify / config |

## Impact / ripple analysis   <!-- cross-repo/cross-module features; else delete -->
| Change | Consumers affected | Mitigation |
| --- | --- | --- |

## References
- System context: `./SYSTEM-CONTEXT.md`
- Testcases (agreed BEFORE implementation): `./testcases.md`
- Task specs: `./tasks/`

## Global acceptance criteria
- [ ] <feature-level outcome 1>
- [ ] <feature-level outcome 2>

## Testcase gate
- [ ] User has reviewed and agreed to `testcases.md`. **Execution must not start before this
      box is ticked.**

## Tasks
<!-- The orchestrator reads this table to sequence and dispatch work. Keep status current.
     Order producer/contract side before consumers. -->

| id | title | repo | depends_on | model | risk | status |
|----|-------|------|-----------|-------|------|--------|
| task-001 | <title> | <repo-a> | — | haiku | low | todo |
| task-002 | <title> | <repo-a> | task-001 | sonnet | high | todo |
| task-003 | <title> | <repo-b> | task-002 | haiku | low | todo |

## Parallelization
<!-- Groups of tasks with no shared files and no mutual dependency can run concurrently. -->
- After task-001 completes: task-002 and task-003 can run in parallel.

## After execution / merge
- [ ] Write guard re-locked (e.g. grant file deleted), if any
- [ ] Host after-merge steps from Environment run
- [ ] Plan `Status` updated

## Notes / open questions
- <anything the user still needs to decide>
