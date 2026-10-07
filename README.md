# SANFootball Concern-Split Codex Execution Pack

This package decomposes the authoritative SANFootball `AGENTS.md` into **46 narrow, reviewable concern agents** while preserving the original master specification unchanged.

## Why this structure exists

The master file remains the governing contract. The files under `agents/` are execution slices, not replacements for it. Their purpose is to let Codex implement one concern at a time so a human reviewer can inspect migrations, tests, architecture, and changed files before the next dependent concern begins.

## Control model

1. `AGENTS.md` is authoritative and must always be read first.
2. `SUBAGENT_ORCHESTRATOR.md` defines the execution/approval protocol.
3. `SANFOOTBALL_IMPLEMENTATION_STATUS.md` is the **single implementation-status document** required by the master specification.
4. Pick **one** concern whose dependencies are `APPROVED`.
5. Codex changes that concern to `IN_PROGRESS`, implements only that scope, then changes it to `READY_FOR_REVIEW`.
6. Codex **must stop** at `READY_FOR_REVIEW`. It may never self-promote to `APPROVED`.
7. After you inspect the work, change the concern to `APPROVED` (or send it back to `IN_PROGRESS`/`BLOCKED`).
8. Only then may a dependent concern start.

Allowed statuses: `NOT_STARTED` · `READY` · `IN_PROGRESS` · `BLOCKED` · `READY_FOR_REVIEW` · `APPROVED` · `DEFERRED` · `SUPERSEDED`.

## Files

- `AGENTS.md` — untouched authoritative master specification.
- `SUBAGENT_ORCHESTRATOR.md` — Codex coordination, stop conditions, approval protocol, and reporting contract.
- `SANFOOTBALL_IMPLEMENTATION_STATUS.md` — one authoritative execution board and repository status ledger.
- `CODEX_START_PROMPTS.md` — reusable prompts for starting, reviewing, resuming, or rejecting one concern.
- `docs/DEPENDENCY_MAP.md` — dependency waves and graph-readable index.
- `docs/SOURCE_SECTION_MAP.md` — concern-to-master-spec mapping.
- `agents/SF-XX_*.md` — concern-specific implementation agents.

## Recommended use

Start with `SF-00`. Do not ask Codex to “implement everything in the agents folder.” Instead, give it exactly one concern file at a time. This package intentionally turns a huge architecture programme into explicit human approval checkpoints.
