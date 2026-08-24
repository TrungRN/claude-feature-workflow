# Skill feedback — feature-workflow

Defects found in **the workflow itself** while running it, written down so the next feature does
not hit them again. This is not a bug list for the product being built — those belong in the
plan's testcases or in `SYSTEM-CONTEXT.md § Lessons learned`.

**Where this file lives and why:** at the plans root, *outside* `.claude/skills/`. Re-copying the
skill from its source repo overwrites the skill directory; this file is never touched, so
feedback accumulates across features and survives upgrades.

**How it gets applied:** the skill never edits its own installed copy — see the source repo's
README. Open the source repo (`claude-feature-workflow`), point a session at this file, and let
it turn the `open` entries into real edits. Mark each entry `applied <date>` once it lands there,
so the same proposal is not re-applied on the next harvest.

---

## <YYYY-MM-DD> · <short title of the defect>

- **Where**: `<skill file>` § `<heading>`
  <!-- e.g. `assets/task-template.md` § `## Self-check`, or `references/task-spec-standard.md`
       § Haiku-readiness checklist, or `SKILL.md` Phase 4 -->
- **What happened**: <the concrete symptom — which plan, which task id, what the agent did wrong,
  what had to be fixed by hand>
- **Why it will recur**: <what makes this structural rather than a one-off; if you cannot answer
  this, the entry does not belong here>
- **Proposed change**: <the exact edit: the new wording, the field to add, the check to insert.
  Specific enough that someone can apply it without having seen the run.>
- **Severity**: blocker | friction | polish
  <!-- blocker = execution stopped or produced wrong work · friction = cost extra turns or
       manual fixes · polish = wording/clarity -->
- **Status**: open
