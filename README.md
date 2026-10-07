# SANFootball Concern-Split Codex Execution Pack

This package decomposes the SANFootball master implementation programme into **46 narrow, reviewable concern agents** with explicit dependencies and human approval gates.

## Important architecture change in this revised pack

The original 9,000+ line master specification is **no longer the root `AGENTS.md`**.

Instead:

- `AGENTS.md` is now a compact execution/orchestration instruction file intended to be loaded by Codex on every run.
- `docs/specifications/SANFOOTBALL_MASTER_SPECIFICATION.md` contains the **complete original master specification, preserved verbatim**, and remains the architecture/product authority.
- each `agents/SF-XX_*.md` file identifies the master sections relevant to that concern;
- Codex reads only those relevant master sections by default, not the entire master on every task.

This preserves the master specification without wasting context or encouraging Codex to implement unrelated work.

## Control model

1. Root `AGENTS.md` defines the execution protocol.
2. The preserved master specification defines the target architecture and product requirements.
3. `SUBAGENT_ORCHESTRATOR.md` defines the execution/approval protocol in detail.
4. `SANFOOTBALL_IMPLEMENTATION_STATUS.md` is the **single implementation-status document** required by the master specification.
5. Pick **one** concern whose dependencies are `APPROVED`.
6. Codex changes that concern to `IN_PROGRESS`, implements only that scope, then changes it to `READY_FOR_REVIEW`.
7. Codex **must stop** at `READY_FOR_REVIEW`. It may never self-promote to `APPROVED`.
8. After you inspect the work, approve it (or return it to `IN_PROGRESS`/`BLOCKED`).
9. Only then may a dependent concern start.

Allowed statuses: `NOT_STARTED` · `READY` · `IN_PROGRESS` · `BLOCKED` · `READY_FOR_REVIEW` · `APPROVED` · `DEFERRED` · `SUPERSEDED`.

## Files

- `AGENTS.md` — compact Codex operating rules and selective-loading protocol.
- `docs/specifications/SANFOOTBALL_MASTER_SPECIFICATION.md` — untouched authoritative master architecture/product specification.
- `docs/specifications/SANFOOTBALL_MASTER_SPECIFICATION.sha256` — checksum of the preserved master.
- `SUBAGENT_ORCHESTRATOR.md` — coordination, stop conditions, approval protocol, and reporting contract.
- `SANFOOTBALL_IMPLEMENTATION_STATUS.md` — authoritative execution board and repository status ledger.
- `CODEX_START_PROMPTS.md` — reusable prompts, including the recommended first SF-00 prompt.
- `docs/DEPENDENCY_MAP.md` — dependency waves and graph-readable index.
- `docs/SOURCE_SECTION_MAP.md` — concern-to-master-spec mapping.
- `docs/CONCERN_MANIFEST.md` — all 46 concerns and their objectives.
- `agents/SF-XX_*.md` — concern-specific implementation agents.

## How to install into the SANFootball repository

Copy the **contents of this package directory** into the root of the SANFootball repository. Preserve your existing code and review conflicts before overwriting any repository documentation with the same names.

The expected repository-level control files should then include:

```text
AGENTS.md
SUBAGENT_ORCHESTRATOR.md
SANFOOTBALL_IMPLEMENTATION_STATUS.md
CODEX_START_PROMPTS.md
agents/
docs/specifications/SANFOOTBALL_MASTER_SPECIFICATION.md
docs/DEPENDENCY_MAP.md
docs/SOURCE_SECTION_MAP.md
docs/CONCERN_MANIFEST.md
```

## Start here

Open `CODEX_START_PROMPTS.md` and use **Recommended first prompt — start SF-00**.

Do not ask Codex to “implement everything in the agents folder.” The entire structure is designed around one concern → review → approval → next concern.
