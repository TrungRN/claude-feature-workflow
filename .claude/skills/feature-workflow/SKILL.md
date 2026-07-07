---
name: feature-workflow
description: >-
  Plan AND execute a feature, in any host: a single repo, or a multi-repo workspace described
  by a knowledge base. Turns a feature request / URD / spec / ticket into a plan, testcases
  written BEFORE code, and small self-contained task specs that a cheaper model can execute;
  then dispatches task-executor / task-executor-pro subagents per task tier and independently
  checks results with task-verifier. Use whenever the user wants to plan, spec out, break
  down, or build a feature (a pasted URD/ticket plus intent to build is enough — the word
  "plan" is not required), or asks to execute / resume / continue a plan under plans/.
argument-hint: "<feature description>"
---

# Feature Workflow

One skill drives the whole feature lifecycle:

**plan with a strong model → testcases first → execute with tiered executors →
verify independently.**

The session running this skill does the hard thinking: it reads the requirements, analyzes
impact (through a knowledge base when one exists — far cheaper than raw code), and decomposes
the work. The output artifacts are engineered so that a cheaper executor can implement each
task correctly **without guessing**: every task spec must be self-contained per
`references/task-spec-standard.md` — that file is the heart of this skill.

The feature request comes from the invocation arguments; if empty, ask the user to describe it.

## Phase 0 — Detect the host environment

This skill is installed unmodified into different hosts, and may be invoked **away from the
host's root** (e.g. from a workspace root that received a copy of the engine, where the host's
CLAUDE.md was never auto-loaded). Before anything else, settle the five environment facts below
and record them in PLAN.md's `## Environment` section (so a later session can resume execution
without re-deriving them):

1. **mode** — `single-repo` or `kb-workspace`.
2. **host root & plans root** — which directory owns the workflow (record it as an absolute
   path; every other path is relative to it), and where `plans/<feature-slug>/` lives under it.
3. **code-path convention** — what paths in task specs are relative to.
4. **write guard** — any hook blocking writes, and its documented unlock/lock procedure.
5. **analysis sources** — what to read to find impact and conventions.

Resolve them in this order:

- **Host contract (highest priority).** A **"Feature-workflow host contract"** section states
  all five facts; hosts publish it in their `CLAUDE.md`. This is how a knowledge base (or any
  custom host) plugs this skill in without modifying it. The contract may already be in your
  context (the host's CLAUDE.md auto-loaded, or a wrapper command that read it for you). If
  not, **probe for it** before assuming there is none:
  `grep -l "Feature-workflow host contract" CLAUDE.md */CLAUDE.md ../*/CLAUDE.md 2>/dev/null`
  Exactly one hit → that file's directory is the **host root**; read the section and follow it
  exactly. Several hits → ask the user which host to use.
- **KB heuristic.** No contract, but a directory at `.`, `./*/`, or `../*/` looks like a
  knowledge base describing sibling repos (a repo index/map, cross-repo relationship or impact
  docs, per-repo overviews/manifests) → `kb-workspace` with that directory as host root: plans
  in `<kb>/plans/`, code paths as `../<repo>/…` relative to the KB root, analysis through the
  KB's own docs (cheapest first).
- **Default.** Otherwise → `single-repo`: the current repo is the host root; plans in
  `<repo>/plans/`, code paths relative to the repo root, analysis directly on the codebase.

## Ground rules (all modes)

- **Self-contained specs.** A dispatched executor subagent runs in an **isolated context**: it
  does not inherit CLAUDE.md, the KB, or project memory. `SYSTEM-CONTEXT.md` + the task spec
  are the only context it is guaranteed to have — copy every rule a task depends on into them.
- **Testcases before implementation.** Execution does not start until the user agrees to the
  testcases.
- **Ask when ambiguous.** Scope, UX, which repos/modules are in or out, contract shape — STOP
  and ask with concrete options before planning further. Don't guess architecture-significant
  choices; don't ask what the code or KB already answers.
- **Respect enforcement.** Hooks and tool-scoping are the host's hard security layer, applied
  to executors' tool calls too. Never bypass a write guard (e.g. via Bash redirects); if the
  host contract defines an unlock procedure, that is the only door. A denied tool call is
  reported, not routed around.
- **Cheap analysis.** Read the smallest thing that answers the question, stop early, and
  delegate heavy exploration to the read-only `Explore` subagent.

## Phase 1 — Understand the requirements

Read the URD / request / ticket (from disk if attached). Write down in your own words: the
**Goal** (1–3 sentences), **In scope / out of scope**, **Acceptance criteria**, and **Open
questions**. If an open question materially changes the plan, ask the user now. If the host
has reusable playbooks for recurring operations, check them before deriving steps yourself.

## Phase 2 — Analyze impact

Follow `references/analysis.md` for the mode you detected:

- **kb-workspace**: index → relationships/impact docs → per-repo overviews → per-repo
  manifests (verbatim build/test commands) → targeted source only for what the feature
  touches. Confirm the affected-repo set and the ripple ("change X → review Y").
- **single-repo**: locate the modules, types, and conventions the feature interacts with — and
  stop; don't map the whole repo.

Then pick the path: **small & unambiguous** (one repo/module, no contract change) →
lightweight run — short PLAN, few tasks, still testcases-first. **Large / cross-repo /
ambiguous** → full path; resolve open questions with the user first.

## Phase 3 — Capture the system context

Write `plans/<slug>/SYSTEM-CONTEXT.md` per `references/analysis.md`: relevant modules, key
types (quoted inline), the **conventions** the feature must follow (from CLAUDE.md files,
rules docs, observed code — per repo in kb-workspace mode), the **verbatim build/test/lint
commands**, integration points/contracts, and constraints. This file is the executors' only
source of house style — make it earn that.

## Phase 4 — Decompose, tier, write testcases and the plan

- Break the work into the smallest independently-implementable, independently-verifiable
  units: **one concern per task** (and one repo per task in kb-workspace mode),
  dependency-ordered (producer/contract side before consumers), parallel-friendly, small
  enough for one executor context.
- Tag each task: **`model`** — `haiku` for mechanical/bounded work, `sonnet` for real logic,
  ambiguity, or new components/architecture. **`risk`** — `high` for auth, payments,
  migrations, security, data-loss, or a cross-module/cross-repo **contract change**; `low`
  otherwise. `risk` drives verifier tier.
- **Write `plans/<slug>/testcases.md` FIRST** — from the host's testcase template if its
  contract names one, else `assets/testcases-template.md`: happy path, edge cases, errors,
  integration.
- Write one spec per task from `assets/task-template.md`, following
  `references/task-spec-standard.md` exactly; run every spec through the **Haiku-readiness
  checklist**. Constraints must state the specific conventions; tasks that create new files
  must include a **"Pattern to mirror"** quoted inline.
- Write `plans/<slug>/PLAN.md` from `assets/PLAN-template.md`: summary, **Environment**
  (Phase 0 facts), affected repos/modules, impact, ordered task table
  (`repo`/`model`/`risk`/`status`), parallelization groups, global acceptance criteria, the
  testcase gate, and after-merge steps from the host contract.
- **STOP.** Present plan + testcases for approval. Implementation does not start until the
  user agrees to the testcases (tick the gate in PLAN.md).

## Phase 5 — Execute (unlock → dispatch → verify → lock)

Only after explicit user approval:

1. **Unlock (if the host has a write guard).** Perform exactly the unlock procedure in the
   host contract / PLAN.md Environment — e.g. a grant file listing only the plan's repos.
   Never widen it beyond the plan; re-lock the moment execution stops, for any reason. No
   guard → skip.
2. **Dispatch.** From PLAN.md, find tasks whose `depends_on` are all `done`. Route by tier:
   `model: haiku` → **task-executor**; `model: sonnet` → **task-executor-pro**. Pass the
   **absolute paths** of the task file and SYSTEM-CONTEXT.md, plus the root that spec paths
   are relative to (from Environment). Dispatch independent ready tasks in the same turn to
   run them in parallel.
3. **Verify.** Every completed task goes to **task-verifier**; `risk: high` tasks go to
   **task-verifier-pro** (Opus). On **FAIL**: re-dispatch the same-tier executor with the
   verifier's feedback appended; after 2 fails, escalate the executor one tier or surface to
   the user. On **PASS**: mark the task `done` in PLAN.md.
4. **Lock.** When all tasks are `done` or genuinely blocked: undo the unlock (e.g. delete the
   grant file), set the plan `Status`, and surface blockers.
5. **Close the loop.** Run the host's after-merge steps from the contract (e.g. refresh the
   KB, rebuild relationship docs, record an ADR). No contract → just remind the user to
   commit/review.

If the executor/verifier agents are not installed in this host (`.claude/agents/`), say so and
offer: (a) install them from this package, or (b) degraded mode — execute the tasks yourself,
sequentially, still spec-by-spec with self-checks.

State once to the user: multi-agent execution uses several times the tokens of a single
session; tiering (cheap doers for cheap work, strong models only where they earn it) is what
keeps that reasonable.

## Model strategy

- **Executors:** `task-executor` = Haiku (well-specified mechanical tasks); `task-executor-pro`
  = Sonnet (logic-heavy, ambiguous, new-architecture tasks). The planner chooses per task via
  the `model` field.
- **Verifiers:** `task-verifier` = Sonnet by default; `task-verifier-pro` = Opus, reserved for
  `risk: high`. Opus-on-everything gives diminishing returns — reserve it as the escalation
  tier (high-risk review, or the retry after two failures).

## Quality bar before handing off a plan

Re-read each spec as if you were the executor with no other context: *could I do exactly this,
correctly, from the spec alone — including its stated conventions — without opening any file
that isn't quoted in it?* Fix any task where the answer is no.

## Reference files

- `references/task-spec-standard.md` — task spec format + Haiku-readiness checklist. **Read
  before writing any task.**
- `references/analysis.md` — impact analysis (with or without a KB) + SYSTEM-CONTEXT.md.
- `assets/task-template.md` — copy per task. `assets/PLAN-template.md` — copy for PLAN.md.
- `assets/testcases-template.md` — copy for testcases.md (unless the host names its own).

Dispatched by this skill (in `.claude/agents/`): `task-executor` (Haiku), `task-executor-pro`
(Sonnet), `task-verifier` (Sonnet), `task-verifier-pro` (Opus, `risk: high`).
