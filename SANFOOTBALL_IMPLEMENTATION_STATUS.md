# SANFootball Implementation Status

> **Authoritative execution ledger.** This is the single repository-wide implementation-status document required by `docs/specifications/SANFOOTBALL_MASTER_SPECIFICATION.md`. Root `AGENTS.md` governs how Codex uses it. Do not create competing phase/status files.

## Current Master Phase

Baseline / not yet started.

## Current Subphase

`SF-00 — Baseline & Repository Characterization`

## Concern Execution Board

Allowed statuses: `NOT_STARTED` · `READY` · `IN_PROGRESS` · `BLOCKED` · `READY_FOR_REVIEW` · `APPROVED` · `DEFERRED` · `SUPERSEDED`.

| ID | Concern | Dependencies | Status | Reviewer / Approval Ref | Notes / Blocker |
|---|---|---|---|---|---|
| SF-00 | Baseline & Repository Characterization | — | `READY` | — | — |
| SF-01 | Characterization Test Safety Net | SF-00 | `NOT_STARTED` | — | — |
| SF-02 | Settings, Secrets & Environment Configuration | SF-00 | `NOT_STARTED` | — | — |
| SF-03 | Dependency, Runtime & Process Isolation | SF-02 | `NOT_STARTED` | — | — |
| SF-04 | Legacy Framework & API Structure Removal | SF-01, SF-02 | `NOT_STARTED` | — | — |
| SF-05 | Identity, Authentication & Authorization Foundation | SF-01, SF-02 | `NOT_STARTED` | — | — |
| SF-06 | Podcast Content & Sports Metadata Canonicalization | SF-04 | `NOT_STARTED` | — | — |
| SF-07 | Plan, Price, Subscription & Entitlement Models | SF-05, SF-06 | `NOT_STARTED` | — | — |
| SF-08 | Canonical Access Policy | SF-07 | `NOT_STARTED` | — | — |
| SF-09 | Billing Provider & Webhook Lifecycle | SF-08 | `NOT_STARTED` | — | — |
| SF-10 | Playback Progress & Continue Listening | SF-05, SF-06 | `NOT_STARTED` | — | — |
| SF-11 | Queue / Up Next Rewrite | SF-10 | `NOT_STARTED` | — | — |
| SF-12 | Library: Follows, Playlists & Bookmarks | SF-10, SF-11 | `NOT_STARTED` | — | — |
| SF-13 | Media Asset Model & Cloudflare Provider Boundary | SF-03, SF-06, SF-08 | `NOT_STARTED` | — | — |
| SF-14 | Direct Upload, Protected Delivery & Media Lifecycle | SF-13, SF-08 | `NOT_STARTED` | — | — |
| SF-15 | Transcription, Chapters, Summaries & AI Baseline | SF-13 | `NOT_STARTED` | — | — |
| SF-16 | Community & Moderation | SF-05, SF-06 | `NOT_STARTED` | — | — |
| SF-17 | Analytics Events & Transactional Publication | SF-05, SF-06 | `NOT_STARTED` | — | — |
| SF-18 | Discovery, Search, Recommendation & Editorial | SF-06, SF-12, SF-17 | `NOT_STARTED` | — | — |
| SF-19 | Offline / Downloads & Legacy DRM De-risking | SF-08, SF-14 | `NOT_STARTED` | — | — |
| SF-20 | Core Refactor Hardening Gate | SF-02, SF-03, SF-04, SF-05, SF-06, SF-07, SF-08, SF-09, SF-10, SF-11, SF-12, SF-13, SF-14, SF-15, SF-16, SF-17, SF-18, SF-19 | `NOT_STARTED` | — | — |
| SF-21 | Application Compute & Worker Topology | SF-20 | `NOT_STARTED` | — | — |
| SF-22 | Database, Cache, Broker & Search Hosting | SF-20 | `NOT_STARTED` | — | — |
| SF-23 | Edge, CDN & Object-Storage Security | SF-14, SF-20 | `NOT_STARTED` | — | — |
| SF-24 | Networking, Secrets & Least Privilege | SF-21, SF-22, SF-23 | `NOT_STARTED` | — | — |
| SF-25 | IaC, CI/CD, Releases & Environments | SF-21, SF-22, SF-23, SF-24 | `NOT_STARTED` | — | — |
| SF-26 | Backup, Restore & Disaster Recovery | SF-22, SF-25 | `NOT_STARTED` | — | — |
| SF-27 | Observability, Reliability, Capacity & FinOps | SF-21, SF-22, SF-23 | `NOT_STARTED` | — | — |
| SF-28 | Production Infrastructure Acceptance Gate | SF-21, SF-22, SF-23, SF-24, SF-25, SF-26, SF-27 | `NOT_STARTED` | — | — |
| SF-29 | Advanced Player | SF-28 | `NOT_STARTED` | — | — |
| SF-30 | Smart Library & Smart Downloads | SF-29 | `NOT_STARTED` | — | — |
| SF-31 | Cross-Device Playback & Active Session | SF-30 | `NOT_STARTED` | — | — |
| SF-32 | RSS & OPML Portability | SF-31 | `NOT_STARTED` | — | — |
| SF-33 | Clips & Quote Cards | SF-32 | `NOT_STARTED` | — | — |
| SF-34 | Video Podcasts & Media Variants | SF-33 | `NOT_STARTED` | — | — |
| SF-35 | Football Intelligence & Content Knowledge Graph | SF-34 | `NOT_STARTED` | — | — |
| SF-36 | Semantic Search / Ask SANFootball | SF-35 | `NOT_STARTED` | — | — |
| SF-37 | Intelligent Notifications, Personalised Home & Highlights | SF-36 | `NOT_STARTED` | — | — |
| SF-38 | Creator & Subscription Conversion Analytics | SF-37 | `NOT_STARTED` | — | — |
| SF-39 | Networks, Creator Teams & Advanced Commercial Packaging | SF-38 | `NOT_STARTED` | — | — |
| SF-40 | Live Podcasting | SF-39 | `NOT_STARTED` | — | — |
| SF-41 | Matchday Rooms, Chapters & Listen-Around-the-Match | SF-40 | `NOT_STARTED` | — | — |
| SF-42 | Listener Stats, Annual Recap & Achievements | SF-41 | `NOT_STARTED` | — | — |
| SF-43 | Connected Devices & Low-Bandwidth Experience | SF-42 | `NOT_STARTED` | — | — |
| SF-44 | Transcript Translation, Accessibility & Creator AI | SF-43 | `NOT_STARTED` | — | — |
| SF-45 | Final System Hardening, End-to-End Acceptance & Cleanup | SF-44 | `NOT_STARTED` | — | — |

## Baseline / Inventory

_To be populated by SF-00._

## Completed

_None yet._

## Verified Existing Implementations

_None recorded yet._

## In Progress

_None yet._

## Deferred

_None._

## Blocked

_None._

## Legacy Components Remaining

_To be populated from repository inspection._

## Data Migrations

| Migration / Backfill | Concern | State | Reversible / Rollback | Verification |
|---|---|---|---|---|

## Backfills

| Backfill | Concern | State | Idempotent? | Verification |
|---|---|---|---|---|

## Compatibility Routes / Contracts

| Contract | Concern | Compatibility Strategy | Removal/Review Condition |
|---|---|---|---|

## Canonical Owners Established

| Concept | Canonical Owner | Concern | Evidence |
|---|---|---|---|

## Infrastructure Decisions

| Decision | Concern / ADR | Status | Notes |
|---|---|---|---|

## Hosting / Deployment Status

_To be populated._

## Media Storage / CDN Status

_To be populated._

## Database / Cache / Broker Status

_To be populated._

## Queue / Worker Capacity Status

_To be populated._

## Backup / Restore / DR Status

_To be populated._

## Observability / Alerts Status

_To be populated._

## IaC / CI/CD Status

_To be populated._

## Security / Privacy Risks

| Risk | Severity | Concern | Owner | Exit Condition |
|---|---|---|---|---|

## Cost / Capacity Risks

| Risk | Concern | Measurement | Threshold / Exit Condition |
|---|---|---|---|

## Tests / Quality Gates

| Concern | Command / Suite | Result | Date/Commit | Notes |
|---|---|---|---|---|

## ADRs

| ADR | Concern | Status | Summary |
|---|---|---|---|

## Known Risks

_None recorded yet._

## Review / Approval Log

> Only a human/reviewer may add an `APPROVED` entry.

| Concern | Decision | Reviewer | Date/Commit | Review Notes |
|---|---|---|---|---|

## Next Actions

1. Execute `SF-00` only.
2. When it reaches `READY_FOR_REVIEW`, stop for human inspection.
3. After human approval, mark `SF-00` `APPROVED` and refresh the next `READY` concern(s).
