# Impact Analysis & System Context

Goal: understand *only what this feature touches*, at the lowest token cost the host allows,
and capture the shared parts once in `plans/<slug>/SYSTEM-CONTEXT.md` so you don't re-derive
them per task.

## Mode A — the workspace has a knowledge base (`kb-workspace`)

A KB exists precisely so you don't have to explore raw source. Read its docs tiered, cheapest
first, and stop as soon as you have enough. If the host contract names the exact files, use
those; the generic shape (e.g. the agent-knowledge-base scaffold) is:

1. **Repo index** (e.g. `INDEX.md`) — what every repo is; pick candidates. Never read past it
   for repos it rules out.
2. **Relationship / impact docs** (e.g. `relationships.md`) — contracts between repos + the
   impact table ("change X → review Y"). This is where "affected repos", the ripple, and the
   execution order (producer/contract repos before consumers) come from.
3. **Per-repo overviews** (e.g. `repos/<r>/overview.md`) — candidates only: purpose, entry
   points, key dirs, human notes.
4. **Per-repo manifests** (e.g. `repos/<r>/manifest.json`) — the **verbatim** run/test/lint
   commands and exact produced/consumed contracts. Every task's Self-check reuses these
   commands — take them from here, don't re-derive them.
5. **Source in `../<repo>/…`** — only the files the feature actually touches, to quote them
   into task specs.

If the KB looks stale for an affected repo (recorded HEAD ≠ actual `git -C ../<repo> rev-parse
HEAD`), tell the user and suggest refreshing the KB before planning on top of it.

## Mode B — no knowledge base (`single-repo`)

Analyze the codebase directly, with the same discipline:

- **Relevance over completeness.** Don't map the whole repo. Find the modules, types, and
  conventions the feature interacts with, and stop.
- **Delegate heavy reading.** For a large codebase, spawn the built-in `Explore` subagent
  (read-only) to locate call sites and summarize structure, then synthesize its result. This
  keeps your own context clean.
- Get build/test/lint commands from package scripts / Makefile / CI config / CLAUDE.md —
  verbatim.

## Both modes

- **Settle the UI surface while you're in the manifests.** Classify the feature's user-facing
  surface as `web`, `mobile`, or `none` and record it in PLAN.md `## Environment`. The evidence is
  in files you're already reading: web framework deps / `public/` / a dev-server script → `web`;
  react-native/expo/flutter deps, `ios/`, `android/`, `*.xcodeproj` → `mobile`; a backend, CLI, or
  library → `none`. In kb-workspace mode the per-repo overview usually states this outright.
- **Capture the app-start command too, not just build/test/lint.** Every task with a UI check
  needs it verbatim — the dev-server command plus the URL for web, or the app id / build path and
  target device for mobile. Getting it wrong is the most common reason a UI check degrades to
  `NEEDS-HUMAN`, so take it from the manifest rather than guessing.
- **Compact and reusable.** `SYSTEM-CONTEXT.md` is a reference, not a dump. Quote the small,
  load-bearing bits; use paths for the rest.
- **Don't maintain a directory tree.** Trees go stale instantly; task specs quote exact files.
- **Capture the rules, don't assume them.** Read all applicable `CLAUDE.md` files (they stack
  up the directory tree), `.claude/rules/` or convention docs, and — in kb-workspace mode —
  the KB's cross-repo convention docs. A dispatched executor inherits **none** of these: what
  tasks must follow has to be written into `SYSTEM-CONTEXT.md` and the specs.
- If a design/HTML mockup is provided, extract the concrete UI contract (component structure,
  states, copy, tokens) rather than describing it loosely.

## What to capture

- **Affected repos/modules + role of each** (producer / consumer / UI / config-only).
- **Relevant files** and what each is responsible for.
- **Key types / interfaces / schemas / contracts** the feature reads or extends (quote them).
- **Conventions**: styling, error handling, state/data, logging, naming, testing.
- **Build / test / lint commands** — verbatim, with their working directory.
- **How to run the app** — verbatim, when the UI surface isn't `none`: the dev-server command and
  the URL it serves, or the app id / build path and target device.
- **Integration points**: APIs, events, feature flags, auth, components to reuse.
- **Constraints**: things not to break (impact table / observed), performance/security limits,
  deprecated paths.

## SYSTEM-CONTEXT.md template

In single-repo mode, drop the per-repo split and the contracts section if there are none.

```markdown
# System Context — <feature>

## Affected repos / modules
| Repo or module | Role in this feature | Why (contract/impact) |
| --- | --- | --- |

## Contracts touched
<quote the contract shapes: endpoint/event/schema — and who produces/consumes them>

## Per repo: <name>   <!-- single-repo mode: just one section, no ../ prefix -->
### Relevant modules
- `<path>` — responsibility
### Key types / interfaces
<quote the small, load-bearing definitions>
### Conventions this feature must follow
<!-- Distilled from CLAUDE.md / rules / observed code. Executors rely on THIS. -->
- Styling: … / Errors: … / State & data: … / Naming: … / Testing: …
### Commands (verbatim; state the working directory)
- Typecheck: `…` / Lint: `…` / Test (scoped): `…`
### Running the app   <!-- omit when the UI surface is `none` -->
- Web: start `…` in `…` → serves `http://localhost:…`
- Mobile: app id `…` / build `…`, target device `…`

## Integration points
- …

## Constraints / do-not-break
- …

## Lessons learned
<!-- Seeded at Phase 3 from `<plans root>/LESSONS.md` — the entries that apply to the repos this
     feature touches, copied in verbatim (executors read this file and nothing else). Empty when
     that file doesn't exist yet.
     During execution the orchestrator appends one line per FAIL whose cause could hit another
     task too (a convention, a lint rule, a gotcha the plan didn't state). Executors run in
     isolated contexts and all read this file, so this is the only place a lesson propagates.
     State each as a rule, not as a story about the task that hit it. At Phase 5 step 7 the
     durable ones are promoted back to `<plans root>/LESSONS.md` for the next feature. -->
- (carried from LESSONS.md · <repo>) <rule>
- (task-00X) <rule a fresh executor can follow without knowing what happened>
```
