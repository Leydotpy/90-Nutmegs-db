# Dependency Map

The default path follows the master dependency order. Some early refactor concerns can be inspected in parallel, but implementation remains one-concern-at-a-time unless the user explicitly authorizes parallel work.

## Concern index

| ID | Concern | Depends on |
|---|---|---|
| SF-00 | Baseline & Repository Characterization | — |
| SF-01 | Characterization Test Safety Net | SF-00 |
| SF-02 | Settings, Secrets & Environment Configuration | SF-00 |
| SF-03 | Dependency, Runtime & Process Isolation | SF-02 |
| SF-04 | Legacy Framework & API Structure Removal | SF-01, SF-02 |
| SF-05 | Identity, Authentication & Authorization Foundation | SF-01, SF-02 |
| SF-06 | Podcast Content & Sports Metadata Canonicalization | SF-04 |
| SF-07 | Plan, Price, Subscription & Entitlement Models | SF-05, SF-06 |
| SF-08 | Canonical Access Policy | SF-07 |
| SF-09 | Billing Provider & Webhook Lifecycle | SF-08 |
| SF-10 | Playback Progress & Continue Listening | SF-05, SF-06 |
| SF-11 | Queue / Up Next Rewrite | SF-10 |
| SF-12 | Library: Follows, Playlists & Bookmarks | SF-10, SF-11 |
| SF-13 | Media Asset Model & Cloudflare Provider Boundary | SF-03, SF-06, SF-08 |
| SF-14 | Direct Upload, Protected Delivery & Media Lifecycle | SF-13, SF-08 |
| SF-15 | Transcription, Chapters, Summaries & AI Baseline | SF-13 |
| SF-16 | Community & Moderation | SF-05, SF-06 |
| SF-17 | Analytics Events & Transactional Publication | SF-05, SF-06 |
| SF-18 | Discovery, Search, Recommendation & Editorial | SF-06, SF-12, SF-17 |
| SF-19 | Offline / Downloads & Legacy DRM De-risking | SF-08, SF-14 |
| SF-20 | Core Refactor Hardening Gate | SF-02, SF-03, SF-04, SF-05, SF-06, SF-07, SF-08, SF-09, SF-10, SF-11, SF-12, SF-13, SF-14, SF-15, SF-16, SF-17, SF-18, SF-19 |
| SF-21 | Application Compute & Worker Topology | SF-20 |
| SF-22 | Database, Cache, Broker & Search Hosting | SF-20 |
| SF-23 | Edge, CDN & Object-Storage Security | SF-14, SF-20 |
| SF-24 | Networking, Secrets & Least Privilege | SF-21, SF-22, SF-23 |
| SF-25 | IaC, CI/CD, Releases & Environments | SF-21, SF-22, SF-23, SF-24 |
| SF-26 | Backup, Restore & Disaster Recovery | SF-22, SF-25 |
| SF-27 | Observability, Reliability, Capacity & FinOps | SF-21, SF-22, SF-23 |
| SF-28 | Production Infrastructure Acceptance Gate | SF-21, SF-22, SF-23, SF-24, SF-25, SF-26, SF-27 |
| SF-29 | Advanced Player | SF-28 |
| SF-30 | Smart Library & Smart Downloads | SF-29 |
| SF-31 | Cross-Device Playback & Active Session | SF-30 |
| SF-32 | RSS & OPML Portability | SF-31 |
| SF-33 | Clips & Quote Cards | SF-32 |
| SF-34 | Video Podcasts & Media Variants | SF-33 |
| SF-35 | Football Intelligence & Content Knowledge Graph | SF-34 |
| SF-36 | Semantic Search / Ask SANFootball | SF-35 |
| SF-37 | Intelligent Notifications, Personalised Home & Highlights | SF-36 |
| SF-38 | Creator & Subscription Conversion Analytics | SF-37 |
| SF-39 | Networks, Creator Teams & Advanced Commercial Packaging | SF-38 |
| SF-40 | Live Podcasting | SF-39 |
| SF-41 | Matchday Rooms, Chapters & Listen-Around-the-Match | SF-40 |
| SF-42 | Listener Stats, Annual Recap & Achievements | SF-41 |
| SF-43 | Connected Devices & Low-Bandwidth Experience | SF-42 |
| SF-44 | Transcript Translation, Accessibility & Creator AI | SF-43 |
| SF-45 | Final System Hardening, End-to-End Acceptance & Cleanup | SF-44 |

## Execution waves

### Wave A — Baseline and safety
`SF-00 → SF-01`, with configuration work beginning from the approved baseline.

### Wave B — Core canonicalisation
`SF-02 … SF-19`, converging settings, identity, content, commercial state, access, billing, playback, media, community, events, discovery and downloads.

### Wave C — Core refactor approval
`SF-20` validates the canonicalisation programme before feature expansion.

### Wave D — Production infrastructure foundation
`SF-21 … SF-28` establishes the Stage-I production-safe hosting boundary and acceptance gate.

### Wave E — Product expansion
`SF-29 … SF-44` follows the master feature phase order.

### Wave F — Final acceptance
`SF-45` closes end-to-end, cleanup, documentation and production-readiness review.

## Important
A concern becoming technically complete does **not** unlock dependents until its status is `APPROVED`. This is deliberate so the user can inspect Codex changes incrementally.
