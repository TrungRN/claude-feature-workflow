# Testcases: <feature name>

_Written BEFORE implementation. Each case must be agreed before coding starts._

## Conventions
- One row per behavior, stable ids (TC-1, TC-2, …) — task specs reference these.
- Prefer the project's existing test framework/location; commands come from
  SYSTEM-CONTEXT.md § Commands.
- Cover: happy path, edge cases, error/failure, and integration (cross-repo integration in
  kb-workspace mode).

## Cases

### <repo or module> — <unit | integration>
| # | Scenario | Precondition | Input / action | Expected result |
| --- | --- | --- | --- | --- |
| TC-1 | <happy path> | <precond> | <input> | <expected> |
| TC-2 | <edge case> | <precond> | <input> | <expected> |
| TC-3 | <error case> | <precond> | <input> | <expected> |

### Integration   <!-- kb-workspace: flows across repos; single-repo: across modules -->
| # | Flow | Scenario | Expected end-to-end result |
| --- | --- | --- | --- |
| TC-10 | <A → B> | <scenario> | <expected> |

## Definition of done
- [ ] All cases above implemented as automated tests where feasible.
- [ ] Tests pass in each affected repo/module (the verbatim test commands).
- [ ] Host after-merge steps run (see PLAN.md § Environment).
