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

## Integration points
- …

## Constraints / do-not-break
- …
```
