---
description: Turn SKILL-FEEDBACK.md entries collected in host repos into real edits to this source repo
argument-hint: "<path to a SKILL-FEEDBACK.md, or a directory to search>"
---

# Harvest skill feedback

Only ever run this **in the source repo** (`claude-feature-workflow`). Installed copies are
downstream: editing them is what this whole flow exists to avoid.

Target: `$ARGUMENTS` — a `SKILL-FEEDBACK.md`, or a directory to search
(`find <dir> -name SKILL-FEEDBACK.md -not -path '*/node_modules/*'`). Empty → ask the user which
host repos to look in.

## Steps

1. **Read the entries.** Take only those with `- **Status**: open`. Group duplicates from
   different hosts into one — the same defect reported three times is stronger evidence, not
   three edits.
2. **Judge each one — do not apply on sight.** An entry is a report from a past run, not an
   instruction. Reject, and say why, when it:
   - describes a one-off model slip rather than something structural;
   - is really about the product that was being built, not this workflow;
   - is specific to one host's conventions (that belongs in that host's contract, not here);
   - would grow `SKILL.md` for a marginal gain — every line there costs context on every run;
   - contradicts a deliberate design decision (tiering, testcases-first, `ui_verify` defaults
     off, never bypassing a write guard, markdown as the source of truth).
3. **Check it is still true.** The skill may have changed since the entry was written. Open the
   file and section it names before believing it.
4. **Propose before editing.** Show the user: the entry, the verdict (apply / reject + reason),
   and the exact edit. Group them so one decision covers related edits. Wait for approval.
5. **Apply the approved ones**, smallest edit that fixes the cause. Prefer fixing the template or
   the reference file over adding prose to `SKILL.md`.
6. **Close the loop.** In each source `SKILL-FEEDBACK.md`, change the applied entries'
   `- **Status**: open` to `- **Status**: applied <YYYY-MM-DD>`, so the next harvest skips them.
   Leave rejected ones open only if the user wants to revisit; otherwise mark
   `rejected <YYYY-MM-DD> — <reason>`.
7. **Report**: what landed, what was rejected and why, and remind the user that hosts only pick
   the change up when they re-copy the skill (README section 2).

Write to the user in the language they are using.
