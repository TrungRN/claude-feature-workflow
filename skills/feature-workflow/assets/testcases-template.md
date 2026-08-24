# Testcases: <feature name>

_Written BEFORE implementation. Each case must be agreed before coding starts._

## Conventions
- One row per behavior, stable ids (TC-1, TC-2, …) — task specs reference these.
- Prefer the project's existing test framework/location; commands come from
  SYSTEM-CONTEXT.md § Commands.
- Cover: happy path, edge cases, error/failure, and integration (cross-repo integration in
  kb-workspace mode).
- **Say how each case gets proven** in the `Verified by` column: `commands` (an automated test) or
  `UI` (someone has to look at the running app). Every `UI` case must appear in some task's
  `### UI check` block, otherwise nothing will ever check it. Note that `UI` describes the *kind*
  of check, not who runs it: by default (`ui_verify: none`) the user runs it by hand. It only
  becomes automatic on tasks the user opts in at the approval gate.
- Prose is in the plan's language; ids, `Verified by` values, and commands stay English.

## Cases

### <repo or module> — <unit | integration>
| # | Scenario | Precondition | Input / action | Expected result | Verified by |
| --- | --- | --- | --- | --- | --- |
| TC-1 | <happy path> | <precond> | <input> | <expected> | commands |
| TC-2 | <edge case> | <precond> | <input> | <expected> | commands |
| TC-3 | <error case> | <precond> | <input> | <expected> | UI |

### Integration   <!-- kb-workspace: flows across repos; single-repo: across modules -->
| # | Flow | Scenario | Expected end-to-end result | Verified by |
| --- | --- | --- | --- | --- |
| TC-10 | <A → B> | <scenario> | <expected> | commands |

## Definition of done
- [ ] All cases above implemented as automated tests where feasible.
- [ ] Tests pass in each affected repo/module (the verbatim test commands).
- [ ] Every `UI` case is covered by some task's `### UI check` block.
- [ ] Every `UI` case has actually been run — by a verifier on an opted-in task, or by the user by
      hand (PLAN.md § Manual verification queue).
- [ ] Host after-merge steps run (see PLAN.md § Environment).
