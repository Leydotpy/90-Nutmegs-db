# AGENTS.md — SANFootball Controlled Concern Execution

> **Repository:** `Leydotpy/90-Nutmegs-db`  
> **Purpose:** compact Codex operating instructions for the concern-split implementation programme  
> **Architectural authority:** `docs/specifications/SANFOOTBALL_MASTER_SPECIFICATION.md`  
> **Execution ledger:** `SANFOOTBALL_IMPLEMENTATION_STATUS.md`

## 1. How this repository is implemented

SANFootball is implemented through small, reviewable concerns under `agents/`.

Do **not** attempt to implement the complete master specification in one run. Work on one named `SF-XX` concern at a time unless the human reviewer explicitly authorizes a named parallel set.

The full original architecture/product specification is preserved verbatim at:

```text
docs/specifications/SANFOOTBALL_MASTER_SPECIFICATION.md
```

That file remains the architectural and product source of truth. This root `AGENTS.md` is intentionally short so Codex can load the execution rules without repeatedly ingesting the entire master specification.

## 2. Source-of-truth hierarchy

Apply these sources in this order:

1. explicit current user instruction;
2. this root `AGENTS.md` for execution protocol and scope discipline;
3. `docs/specifications/SANFOOTBALL_MASTER_SPECIFICATION.md` for architecture, product, security, migration, data-integrity and production requirements;
4. the active `agents/SF-XX_*.md` for the current concern's implementation scope and acceptance gate;
5. `SANFOOTBALL_IMPLEMENTATION_STATUS.md` for approved/current implementation state;
6. approved ADRs and canonical repository documentation;
7. existing code/tests, after classifying them as canonical, transitional, legacy, missing, or already compliant.

If two sources conflict materially, do not silently choose the easier implementation. Record the conflict in the status ledger and stop if resolving it would change security, data integrity, canonical ownership, public compatibility, production architecture, or an already approved concern.

## 3. Selective master-spec loading rule

For every active concern:

1. read this root file;
2. read `SUBAGENT_ORCHESTRATOR.md`;
3. read `SANFOOTBALL_IMPLEMENTATION_STATUS.md`;
4. read the active concern file in full;
5. read **only** the sections of `docs/specifications/SANFOOTBALL_MASTER_SPECIFICATION.md` listed under that concern's `Master-spec source map`;
6. use `docs/SOURCE_SECTION_MAP.md` as a navigation aid;
7. read additional master sections only when the active concern discovers a material dependency, conflict, security issue, migration issue, or architecture ambiguity that requires them.

Do **not** read the entire master specification on every concern merely because it exists.

`SF-00` is allowed to inspect the master more broadly because its job is repository characterization and architecture mapping, but even SF-00 should use the mapped sections and targeted searches rather than repeatedly loading the whole file when unnecessary.

## 4. One-concern rule

A concern may begin only when all of its listed dependencies are `APPROVED` in `SANFOOTBALL_IMPLEMENTATION_STATUS.md`.

`READY_FOR_REVIEW` does not unlock dependents.

When a concern starts:

- verify dependencies;
- inspect git status/branch/worktree and preserve user changes;
- set only that concern to `IN_PROGRESS`;
- implement only its owned scope;
- record later/adjacent findings instead of implementing them early.

## 5. Human approval gate

Codex may set a concern to:

- `IN_PROGRESS`
- `BLOCKED`
- `READY_FOR_REVIEW`
- `DEFERRED` only when explicitly justified/authorized

Codex MUST NOT mark its own concern `APPROVED`.

When implementation and validation are complete:

1. update `SANFOOTBALL_IMPLEMENTATION_STATUS.md`;
2. set the concern to `READY_FOR_REVIEW`;
3. provide the required review packet from the concern file;
4. STOP.

Only a human reviewer may move it to `APPROVED`.

## 6. No-redo / approved-state rule

Do not reimplement work merely because the preserved master describes the original target state.

If a requirement is already correctly implemented and evidenced by code, tests, constraints, migrations, or an `APPROVED` prior concern:

- verify it;
- record it under `Verified Existing Implementations` where relevant;
- preserve the approved implementation unless a real defect/conflict requires review.

An active concern must not silently rewrite an already `APPROVED` concern. If a prior approved decision blocks safe implementation, set the active concern to `BLOCKED` and document why.

## 7. Canonical architecture rules that always apply

Regardless of concern, preserve the master specification's core invariants:

- one authoritative mutable source of truth for each domain concept;
- no parallel subscription, entitlement, queue, progress, recommendation, media-state or live-state systems;
- explicit service/policy/use-case transitions for critical behavior;
- database constraints/indexes/transactions for real invariants;
- idempotency where retries are normal;
- server-side authorization for protected resources;
- production statelessness and no durable dependency on local media files;
- provider-neutral domain ownership with Cloudflare production integration through `pycflare` where specified;
- direct provider/object-storage transfer for large media where specified;
- bounded queries, no avoidable N+1 paths, and background execution for heavy work;
- secrets/log-redaction/least-privilege requirements;
- safe migrations using expand → backfill → switch → verify → contract when appropriate;
- delete superseded implementations only after data/caller/compatibility verification;
- preserve user data and intentional stable public contracts.

## 8. Required implementation loop

For the active concern use:

```text
inspect → characterize → design → implement → migrate → test → document → observe → remove superseded code → report → STOP FOR APPROVAL
```

Do not create fake placeholders and declare completion. Do not hide unresolved work in TODOs unless explicitly deferred in the status ledger with rationale, risk and dependency.

## 9. Execution/status files

Use these files as the control plane:

```text
SUBAGENT_ORCHESTRATOR.md
SANFOOTBALL_IMPLEMENTATION_STATUS.md
CODEX_START_PROMPTS.md
docs/DEPENDENCY_MAP.md
docs/SOURCE_SECTION_MAP.md
docs/CONCERN_MANIFEST.md
agents/SF-XX_*.md
```

Do not create a second implementation tracker.

## 10. Default entry point

If no concern has yet been approved or started, begin with:

```text
SF-00 — Baseline & Repository Characterization
```

At `READY_FOR_REVIEW`, stop and wait for human approval. Do not automatically continue to `SF-01` or `SF-02`.
