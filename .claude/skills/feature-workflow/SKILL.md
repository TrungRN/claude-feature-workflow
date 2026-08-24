---
name: feature-workflow
description: >-
  Plan AND execute a feature, in any host: a single repo, or a multi-repo workspace described
  by a knowledge base. Turns a feature request / URD / spec / ticket into a plan, testcases
  written BEFORE code, and small self-contained task specs that a cheaper model can execute;
  then dispatches task-executor / task-executor-pro subagents per task tier and independently
  checks results with task-verifier. Execution runs at a cadence the user picks (one task, one
  parallel group, or all) and is resumable: progress is journalled so an interrupted run can be
  continued by a later session or another tool. Use whenever the user wants to plan, spec out,
  break down, or build a feature (a pasted URD/ticket plus intent to build is enough — the word
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

## Phase 0 — Resume, or detect the host environment

**Resume first.** If the user asks to continue/resume a plan (or names one under `plans/`), check
for `plans/<slug>/PROGRESS.md` before deriving anything. If it exists, **read it first** — its
HANDOFF block states where execution stopped and what comes next, which beats re-deriving the
environment. Read PLAN.md's `## Environment` only to confirm those facts, then re-confirm the
execution cadence with the user (keep the recorded mode, or switch) and continue at Phase 5
step 2. Skip the rest of Phase 0.

No PROGRESS.md → settle the environment as follows.

This skill is installed unmodified into different hosts, and may be invoked **away from the
host's root** (e.g. from a workspace root that received a copy of the engine, where the host's
CLAUDE.md was never auto-loaded). Before anything else, settle the seven environment facts below
and record them in PLAN.md's `## Environment` section (so a later session can resume execution
without re-deriving them):

1. **mode** — `single-repo` or `kb-workspace`.
2. **host root & plans root** — which directory owns the workflow (record it as an absolute
   path; every other path is relative to it), and where `plans/<feature-slug>/` lives under it.
3. **code-path convention** — what paths in task specs are relative to.
4. **write guard** — any hook blocking writes, and its documented unlock/lock procedure.
5. **analysis sources** — what to read to find impact and conventions.
6. **UI surface** — `web`, `mobile`, or `none`; settled in Phase 2. It decides which tasks get a
   UI check and which MCP server the verifier needs.
7. **language** — the language of everything a *person* reads: the conversation, every
   `AskUserQuestion`, end-of-unit reports, and artifact prose. Resolve in this order and stop at
   the first that answers:
   a. an explicit instruction from the user (this session, or a CLAUDE.md they control);
   b. `Language:` in the host contract;
   c. the language of **the user's own words** in the request — *not* the language of a pasted
      URD / ticket / spec. A Vietnamese user pasting an English ticket is still a Vietnamese
      user; the paste says nothing about how they want to be talked to;
   d. nothing but pasted material and no prose of their own → **ask**, with `AskUserQuestion`,
      before writing any artifact. One question is cheaper than a whole plan in the wrong language.

Facts 1–5 are resolvable now; 6 comes out of Phase 2, 7 from the rule above.

Resolve them in this order:

- **Host contract (highest priority).** A **"Feature-workflow host contract"** section states
  facts 1–5 and may also pin `Language:`; hosts publish it in their `CLAUDE.md`. This is how a knowledge base (or any
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
- **A user-visible outcome needs a user-visible check — but the user decides who runs it.**
  Passing typecheck and unit tests does not prove a screen behaves correctly, so any task whose
  Definition of Done describes something a person sees or does gets a runnable `### UI check`
  block. Whether a **verifier** drives the real app through that block is the user's call, per
  task, via `ui_verify` — **default `none`**, because driving a browser or a simulator costs real
  tokens and only the user knows which screens are worth it. When it *is* on and the verifier
  can't run it, the honest answer is `NEEDS-HUMAN` — never `PASS` on the command checks alone.
  Never turn `ui_verify` on by yourself.
- **Language: user's language for people, English for machinery.** The value recorded in
  PLAN.md § Environment governs — it is what a later session reads back, since nothing else
  about this conversation survives. Write in that language: conversation, `AskUserQuestion`
  options, end-of-unit reports, and the *prose* inside artifacts
  (Summary, Objective, the text of Definition-of-Done items, scenario descriptions, the HANDOFF
  narrative). Always keep in English: template headings (`## Definition of Done`, `## Self-check`,
  `### UI check`, …), frontmatter field names, every enum value (`todo`/`in-progress`/`done`/
  `blocked`/`needs-human`, `haiku`/`sonnet`, `low`/`high`, `commands`/`browser`/`mobile`), the
  verdicts `PASS`/`FAIL`/`NEEDS-HUMAN`, and all commands, paths, and code identifiers. The reason
  is mechanical: the executor and verifier agents match on those English headings and values, and
  the executors are cheap models that are sensitive to format drift. Translating structure breaks
  the handoff between agents; translating prose is what makes the plan readable to its owner.
- **The user sets the pace.** Execution runs in units the user agreed to (Phase 5). Never run
  past the current unit, even when the next task is ready and nothing is blocking it — the pause
  is what gives the user a window to review the code.
- **Checkpoint before continuing.** `PROGRESS.md` and the `status` fields must describe reality
  before the next unit of work starts, not after. A run can be cut off at any moment; what's on
  disk is all that survives.
- **A repeatable failure is a missing rule.** Executors run in isolated contexts, so a mistake
  one of them makes will be made again by the next one unless the rule is written down. When a
  FAIL turns out to be a convention or a gotcha rather than a one-off slip, append it to
  `SYSTEM-CONTEXT.md` § **Lessons learned** *before* the next dispatch — that file is the only
  thing every executor reads, so this is the one place a lesson actually propagates.
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

While you're in the manifests, settle the **UI surface** (Environment fact 6) — it costs no extra
reading, since the evidence is in files you're already opening:

| Value | Evidence |
|---|---|
| `web` | web framework deps (react/next/vue/svelte/angular), a `public/` or `static/` dir, a dev-server script |
| `mobile` | react-native/expo/flutter deps, an `ios/` or `android/` dir, `*.xcodeproj`, `Podfile` |
| `none` | backend service, CLI, or library — nothing a person looks at |

A feature can touch a UI repo without itself being user-visible (a config or migration task); the
surface describes what's *available* to verify, and Phase 4 decides per task whether to use it.
If a workspace has both a web and a mobile client, record both and tag each task with the one its
repo belongs to.

Then pick the path: **small & unambiguous** (one repo/module, no contract change) →
lightweight run — short PLAN, few tasks, still testcases-first. **Large / cross-repo /
ambiguous** → full path; resolve open questions with the user first.

## Phase 3 — Capture the system context

Write `plans/<slug>/SYSTEM-CONTEXT.md` per `references/analysis.md`: relevant modules, key
types (quoted inline), the **conventions** the feature must follow (from CLAUDE.md files,
rules docs, observed code — per repo in kb-workspace mode), the **verbatim build/test/lint
commands**, integration points/contracts, and constraints. This file is the executors' only
source of house style — make it earn that. End it with an empty `## Lessons learned` section:
Phase 5 appends to it whenever a failure exposes a rule the plan failed to state.

## Phase 4 — Decompose, tier, write testcases and the plan

- Break the work into the smallest independently-implementable, independently-verifiable
  units: **one concern per task** (and one repo per task in kb-workspace mode),
  dependency-ordered (producer/contract side before consumers), parallel-friendly, small
  enough for one executor context.
- Tag each task: **`model`** — `haiku` for mechanical/bounded work, `sonnet` for real logic,
  ambiguity, or new components/architecture. **`risk`** — `high` for auth, payments,
  migrations, security, data-loss, or a cross-module/cross-repo **contract change**; `low`
  otherwise. `risk` drives verifier tier. **`ui_verify`** — always write **`none`**; only the
  user turns it on (see the next bullet).
- Any task with a user-visible Definition-of-Done item gets a `### UI check` block under
  `## Self-check`: how to start the app, numbered deterministic steps, and observable
  expectations tied to testcase ids. Write it **even though `ui_verify: none`** — at `none` it is
  the manual test script, and it is what the user gets handed if the task reaches the Manual
  verification queue. Vague steps make it worthless; write them so a stranger could follow them.
- **Write `plans/<slug>/testcases.md` FIRST** — from the host's testcase template if its
  contract names one, else `assets/testcases-template.md`: happy path, edge cases, errors,
  integration.
- Write one spec per task from `assets/task-template.md`, following
  `references/task-spec-standard.md` exactly; run every spec through the **Haiku-readiness
  checklist**. Constraints must state the specific conventions; tasks that create new files
  must include a **"Pattern to mirror"** quoted inline.
- Write `plans/<slug>/PLAN.md` from `assets/PLAN-template.md`: summary, **Environment**
  (Phase 0 facts), affected repos/modules, impact, ordered task table
  (`repo`/`model`/`risk`/`ui_verify`/`status`), parallelization groups, global acceptance
  criteria, the testcase gate, and after-merge steps from the host contract.
- Render the dashboard (see **Dashboard** below) and hand the user its path with the plan.
- **STOP.** Present plan + testcases for approval. Implementation does not start until the
  user agrees to the testcases (tick the gate in PLAN.md).

  If any task has a `### UI check` block, add a short **UI verification** section to what you
  present — this is the user's one chance to opt in before work starts:

  > These tasks have a UI check that a verifier could run against the real app. It's **off** by
  > default because driving the app costs tokens. Say which ones to turn on:
  > - `task-003` — signup form shows "Invalid email" and disables Submit (TC-3, TC-4) → `browser`
  > - `task-007` — checkout blocks an invalid card (TC-9), `risk: high` → `mobile`

  Give each candidate a one-line reason worth judging — usually `risk: high`, a money/auth flow,
  or a testcase marked `UI` in testcases.md — so the user can decide without opening every spec.
  Set `ui_verify` only on the tasks they name, in both the spec frontmatter and the PLAN.md table.
  Say nothing about UI verification when no task has a UI check.

## Phase 5 — Execute (cadence → unlock → dispatch → verify → lock)

Only after explicit user approval:

1. **Agree the cadence, then open the trail.** Before dispatching anything, ask the user — with
   `AskUserQuestion` — how much work should run between review pauses:

   | Mode | One unit of work is… |
   |---|---|
   | `task-by-task` | a single task |
   | `by-group` *(recommend this)* | one parallel group from PLAN.md `## Parallelization` |
   | `all` | every remaining task |

   Recommend `by-group`: it keeps parallelism while still handing back a reviewable chunk.
   Then record the mode in PLAN.md `## Execution`, apply the approval status writes (see
   **Status discipline**), and create `plans/<slug>/PROGRESS.md` from
   `assets/PROGRESS-template.md`.
2. **Unlock (if the host has a write guard).** Perform exactly the unlock procedure in the
   host contract / PLAN.md Environment — e.g. a grant file listing only the plan's repos.
   Never widen it beyond the plan; re-lock the moment execution stops, for any reason. No
   guard → skip.
3. **Dispatch one unit.** From PLAN.md, find tasks whose `depends_on` are all satisfied (`done`
   or `needs-human` — see below), and take only as many as the agreed mode allows. Route by tier:
   `model: haiku` → **task-executor**; `model: sonnet` → **task-executor-pro**. Pass the
   **absolute paths** of the task file and SYSTEM-CONTEXT.md, plus the root that spec paths are
   relative to (from Environment). Tasks within one unit go out in the same turn, so they run in
   parallel.

   **Before dispatching, check the UI tooling — but only if this unit needs it.** If no task in
   this unit has `ui_verify: browser|mobile`, do nothing here: don't run `claude mcp list`, don't
   mention MCP. A plan with no UI verification turned on never sees this step at all.

   Otherwise run `claude mcp list` and check only the server(s) those tasks need — `browser` →
   `playwright`, `mobile` → `maestro` — is present **and Connected**. Missing → ask the user once,
   with `AskUserQuestion`, combining **whether to install** and **at which scope**: `project`
   writes `.mcp.json` in the host root (committable, the whole team gets it), `user` installs for
   this machine only. Installing touches their repo or their global config, so it is their call —
   never install silently.

   | Server | Install |
   |---|---|
   | `playwright` | `claude mcp add -s <scope> playwright -- npx @playwright/mcp@latest` |
   | `maestro` | needs the Maestro CLI first — check `command -v maestro`; if absent, **stop and ask the user to install it** (docs.maestro.dev), then `claude mcp add -s <scope> maestro -- maestro mcp` |

   Do not install the Maestro CLI yourself: it's a system-level toolchain install, not something
   to do on the user's behalf mid-run. After installing, re-run `claude mcp list` to confirm
   `Connected`. **A newly added MCP server may not reach already-running subagents until the
   session restarts.** If the verifier later reports the tools aren't in its toolset, tell the
   user to restart and re-run the unit — do not let a task pass unverified because the tooling
   arrived late.

   **Record the answer and honor it.** Write `UI tooling: <server> installed (<scope>)` or
   `UI tooling: user declined <server> (<date>)` in PLAN.md `## Execution`. If they declined,
   **never ask again for that server** — go straight to dispatch, and let those tasks come back
   `NEEDS-HUMAN`. Re-asking every unit is exactly the nagging this design exists to avoid.
4. **Verify.** Every completed task goes to **task-verifier**; `risk: high` tasks go to
   **task-verifier-pro** (Opus). Three verdicts:
   - **PASS** → task `done`.
   - **FAIL** → first ask: *could another task hit this same problem?* If yes, append one line
     to `SYSTEM-CONTEXT.md` § **Lessons learned** — stated as a rule a fresh executor can follow,
     not as a story about this task. Then re-dispatch the same-tier executor with the verifier's
     feedback appended; after 2 fails, escalate the executor one tier or surface to the user.
   - **NEEDS-HUMAN** → the code passed every automated check but a user-visible criterion could
     not be machine-verified. Set the task to `needs-human` and add a row to PLAN.md
     `## Manual verification queue` with the criterion, the reason, and the verifier's manual
     steps. **This does not block dependents** — the code is written and its command checks are
     green, so treat it as satisfied for `depends_on` and keep going. It is not a hard stop.

   Record every dispatch and every verdict in PROGRESS.md as it happens, and apply the status
   writes.
5. **Stop and report.** At the end of each unit — including in `all` mode when a stop condition
   below fires — stop, re-render the dashboard (see **Dashboard**), and give the user a compact
   report: which tasks finished, each verdict,
   the files that changed, and the command to review them (`git -C <repo> diff`). List any
   `needs-human` tasks **separately from the `done` ones**, each with what still needs checking
   by hand — burying them in the done pile is how an unverified feature ships. Say what they
   can reply: **continue** · **switch to `all`** · **redo task-00X** · **stop**. Then wait. Do
   not start the next unit unprompted. On **continue**, go back to step 3 with the next unit;
   on a mode change, update PLAN.md `## Execution` first; on **stop**, go to step 6.

   **Hard stops, in every mode including `all`:** a second FAIL on the same task, a task the
   executor reports as blocked, or any tool call denied by a hook. `all` means "don't ask
   between healthy tasks" — it never means "keep going when something is wrong." A
   `NEEDS-HUMAN` verdict is **not** a hard stop; it is a note for later.
6. **Lock.** When every task is `done`, `needs-human`, or genuinely blocked: undo the unlock
   (e.g. delete the grant file), set the plan `Status`, tick the `## After execution` boxes, and
   surface blockers. Leave the **Manual verification queue** box unticked while the queue has
   open rows — only the user can confirm those, so hand them the list and say so plainly.
7. **Close the loop.** Run the host's after-merge steps from the contract (e.g. refresh the
   KB, rebuild relationship docs, record an ADR). No contract → just remind the user to
   commit/review. If `SKILL-FEEDBACK.md` gained entries during this run, say so and point at it
   (see **Improving this skill**) — that is the only moment anyone is likely to act on them.

## Status discipline

The task table in PLAN.md is the **source of truth**; each task spec's `status:` frontmatter is
a mirror that must agree with it. Write the status change **before** reporting it — if the
session dies between the two, the files must not be lying about what happened.

| When | Write |
|---|---|
| User approves plan + testcases | PLAN.md `Status:` → `executing`; tick the **Testcase gate** box; record the mode in `## Execution` |
| A task is dispatched | that task → `in-progress` in **both** the PLAN.md table **and** its spec frontmatter |
| Verifier returns PASS | that task → `done` in both places |
| Verifier returns NEEDS-HUMAN | that task → `needs-human` in both places; add a row to PLAN.md `## Manual verification queue` (criterion · why unverified · manual steps). Dependents may still run |
| Verifier returns FAIL (1st) | leave `in-progress`; journal the specific failure and the retry count in PROGRESS.md; if the cause can repeat elsewhere, append it to SYSTEM-CONTEXT.md § Lessons learned **before** re-dispatching |
| 2nd FAIL, executor blocked, or a denied tool call | that task → `blocked` in both places; stop |
| No tasks left | PLAN.md `Status:` → `done` (or `blocked`); tick the `## After execution` boxes — except the Manual verification queue box, which stays unticked until the user confirms those checks |

**PROGRESS.md** is written continuously, never batched at the end: append a journal line on each
dispatch and each verdict, and rewrite its HANDOFF block at the same time so it always describes
the present moment. That block is what a fresh session — or a different AI, or a human with no
access to this workflow — uses to carry on, so keep it self-contained and absolute-path'd.

## Improving this skill — record, never self-edit

Two different kinds of lesson come out of a run, and they must not be mixed:

| What went wrong | Where it goes | Who reads it |
|---|---|---|
| the **product's** code/conventions surprised an executor | `SYSTEM-CONTEXT.md` § Lessons learned | every later executor, automatically |
| **this workflow** is what failed — a template lacks a field, an instruction is ambiguous enough that a cheap model drifted, a rule doesn't cover a case you hit | `<plans root>/SKILL-FEEDBACK.md` | a human, later, in the skill's source repo |

**Never edit the installed skill during a run** — not `SKILL.md`, not `references/`, not
`assets/`. Three reasons: this copy is downstream of a source repo and re-copying would silently
wipe the edit; a self-edit changes the rules mid-run with nothing reviewing it; and a wrong
self-edit corrupts every future feature, not just this one. Propose, don't patch.

Write an entry when you notice something that will **recur**:

- an executor came back `blocked` because the spec standard has no place for what it needed;
- you had to hand-fix the same kind of drift twice (a heading a cheap model kept mangling);
- a template field was ambiguous, missing, or wrong for this host;
- a rule here gave no answer for a situation that will happen again (a verdict case, a guard
  interaction, a host shape);
- an instruction told you to do something that turned out to be impossible or harmful here.

Do **not** write an entry for a one-off model slip, or for anything specific to this product —
that is what the Lessons learned section is for.

Create the file from `assets/SKILL-FEEDBACK-template.md` on the first entry; append after that.
Each entry names the exact skill file and section, the symptom, why it recurs, and the concrete
proposed edit. Mention the count in the end-of-unit report ("2 mục skill feedback"), so the user
knows there is something to harvest — an entry nobody harvests is worth nothing.

## Dashboard — the plan as one HTML page

The markdown files stay the source of truth: agents read and write those, and only those. On
top of them, `scripts/render-dashboard.py` (stdlib Python 3, no dependencies) builds **one**
derived file for the *user* — `plans/<slug>/dashboard.html`: task cards with status/risk/model
badges, the parallel groups, testcases cross-linked to the tasks that cover them, the manual
verification queue, and the HANDOFF block with a copy button. It also reads the PROGRESS.md
journal back: each task card carries its own attempt/FAIL count and a timeline of what happened
to it, tasks that failed or stalled get a **Needs attention** card, and § Lessons learned is
hoisted out of SYSTEM-CONTEXT.md to the top. No agent ever reads that file, so
it costs no tokens beyond a single Bash call.

```bash
python3 <this-skill-dir>/scripts/render-dashboard.py <the plan dir, or any file in it> --quiet
```

- Run it when Phase 4 finishes PLAN.md, and again at each **Stop and report** in Phase 5, so the
  page never shows a status the files have moved past. Give the user the absolute path the first
  time, and say it is generated — edits belong in the markdown, not in the HTML.
- It **writes** exactly one path — `dashboard.html` inside that plan directory — and only reads
  everything else. It is not a way around a write guard; never point it anywhere else.
- Hosts that install `hooks/render-dashboard.sh` (PostToolUse) get the refresh automatically on
  every write to a plan markdown file, including writes made by subagents.
- No `python3` on the machine, or the script is missing → skip it and say so once. Nothing in
  this workflow depends on the dashboard.

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
- `assets/PROGRESS-template.md` — copy for PROGRESS.md at the start of Phase 5; the execution
  journal + the HANDOFF block that makes a run resumable.
- `scripts/render-dashboard.py` — builds `plans/<slug>/dashboard.html` from the markdown. Run
  it, never read it.
- `assets/SKILL-FEEDBACK-template.md` — copy to `<plans root>/SKILL-FEEDBACK.md` the first time
  this workflow itself proves defective. See **Improving this skill**.

Dispatched by this skill (in `.claude/agents/`): `task-executor` (Haiku), `task-executor-pro`
(Sonnet), `task-verifier` (Sonnet), `task-verifier-pro` (Opus, `risk: high`).
