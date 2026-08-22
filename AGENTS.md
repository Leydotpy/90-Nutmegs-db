# AGENTS.md — SANFootball Unified Master Architecture, Refactor, Feature, and Production Infrastructure Specification

> **Repository:** `Leydotpy/sanfootball`  
> **Project:** SANFootball  
> **Product:** Football-first podcast, sports-audio/video, discovery, community, membership, premium-content, creator, live-media, and football-intelligence platform  
> **Backend baseline:** Django + Django REST Framework  
> **Background processing baseline:** Celery / asynchronous worker architecture  
> **Primary relational database:** PostgreSQL-first  
> **Cache / broker baseline:** Redis/Valkey-compatible architecture, with broker/provider boundaries where specified  
> **Cloudflare media integration baseline:** Cloudflare R2 + Cloudflare Images + Cloudflare Stream, integrated from Python through `pycflare` installed from `https://github.com/Leydotpy/pycflare`  
> **Identity baseline:** Clerk-integrated identity with a canonical local Django domain user, unless the repository has since adopted a newer explicit identity contract  
> **Status:** **SINGLE AUTHORITATIVE ROOT SPECIFICATION**  
> **Consolidated:** 2026-08-19  
> **Cloudflare/pycflare media amendment:** 2026-08-22  
> **Supersedes for this repository:** all earlier SANFootball `AGENTS.md` refactor, post-refactor feature-expansion, and infrastructure-amendment specifications represented in the source documents used to build this file.

---

# A. MASTER AUTHORITY AND CONFLICT RULES

This file is the single governing implementation contract for SANFootball. A coding agent MUST NOT require a separate historical SANFootball `AGENTS.md` in order to understand the intended architecture, the refactor, the feature roadmap, or the production-hosting model.

The repository has two inseparable programmes of work:

1. **Core canonicalisation and modernisation** — remove architectural duplication and establish one authoritative implementation for each domain concept while preserving valuable capability and user data.
2. **Post-refactor product and infrastructure evolution** — add the premium-player, smart-library, football-intelligence, creator, live-media, video, AI, analytics, connected-device, and production-hosting capabilities without recreating the fragmentation that the refactor removes.

The rules below resolve any overlap between the two programmes.

## A.1 Precedence

When two provisions appear to overlap or differ:

1. this master authority section wins;
2. explicit **security, data-integrity, privacy, disaster-recovery, or production-infrastructure** requirements win over older/general wording;
3. the newer production-hosting and infrastructure requirements in Part II govern infrastructure choices made during Part I;
4. the canonical-domain and migration rules in Part I govern how Part II features are integrated into the repository;
5. an existing repository-level instruction newer than this file may override this file only when it is explicit, intentional, and documented;
6. user data and stable public contracts must not be destroyed merely to achieve architectural neatness;
7. compatibility is a migration tool, not permission to retain duplicate architecture indefinitely.

## A.2 Single-source-of-truth rule

The agent MUST maintain one authoritative mutable source of truth for each concept, including but not limited to:

- identity;
- podcast/show, season, episode, chapter, transcript, summary, and media metadata;
- sports/football entities and content links;
- playback progress, queue, playlist, bookmark, library, and download intent;
- plan, price, subscription, membership, entitlement, and access decisions;
- comments, reactions, polls, moderation state, and live-room/community state;
- notification preferences and delivery state;
- creator/network/team ownership and permissions;
- analytics events and derived metrics;
- clip definitions and media derivatives;
- active playback sessions;
- live-broadcast lifecycle;
- media object/provider location and processing state.

A new feature MUST extend the canonical owner rather than create a second model/service/state machine merely because implementation is easier in isolation.

## A.3 Repository inspection is mandatory

This specification defines the target architecture and behavioural contracts; it does **not** assume exact package names, class names, migration numbers, API routes, task names, serializer names, or provider choices currently present in the repository.

Before changing code, the agent MUST inspect the real repository and map these conceptual requirements to the existing implementation. It MUST preserve user changes, inspect git status, trace callers, inspect migrations, inspect tests, and determine which implementations are canonical, legacy, transitional, or missing.

## A.4 Do not redo completed work

If a Part I refactor requirement is already correctly implemented, verified by code/tests/data constraints, the agent MUST NOT rewrite it merely to match a preferred style. Mark it verified and continue.

If it is only partially implemented, complete the missing canonicalisation safely before implementing a dependent feature.

If a Part II feature is already present, the agent MUST audit it against this specification, migrate it into the canonical architecture if necessary, and avoid creating a parallel implementation.

## A.5 Modular monolith is the default

SANFootball remains a modular monolith by default. Domain boundaries, explicit services/policies/selectors, internal events, background workers, storage/provider adapters, and clear transaction boundaries are mandatory. Feature growth alone does not justify microservices.

Heavy media processing, search/indexing, analytics aggregation, machine-learning inference, live-media infrastructure, or other resource-specialised workloads MAY be separately deployable when operational evidence justifies it, but canonical domain ownership and contracts must remain explicit.

## A.6 Production infrastructure applies from the beginning

Part II contains the newer and more detailed production architecture. Those requirements are not a final hosting afterthought. During every Part I change, the agent MUST avoid designs that conflict with the production rules, particularly:

- no durable production dependency on local media files;
- stateless horizontally scalable web compute;
- independent worker scaling;
- direct-to-object-storage/provider upload for large media;
- CDN/edge delivery rather than Django byte transport for normal media playback;
- bounded database/cache/broker connections;
- explicit queue/backpressure behaviour;
- provider adapters instead of provider-specific domain coupling;
- IaC and CI/CD for production infrastructure;
- backup/restore and disaster-recovery planning;
- structured observability, metrics, alerts, tracing where useful, and runbooks;
- secrets and least-privilege permissions;
- cost attribution, storage/bandwidth controls, and FinOps visibility;
- Cloudflare is the selected production media platform for the current implementation: R2 for object storage/audio and general binary assets, Images for managed image upload/transformation/private delivery, and Stream for managed video ingest/encoding/private playback;
- all Python-side Cloudflare integration MUST go through the `pycflare` package and SANFootball provider adapters, not ad-hoc Cloudflare HTTP calls, direct `boto3` usage, or a second Cloudflare SDK integration scattered through domain code.

## A.7 One implementation-status document

Maintain a single repository-wide status document:

```text
SANFOOTBALL_IMPLEMENTATION_STATUS.md
```

It replaces separate refactor and feature-expansion status files. It MUST include at minimum:

```text
# SANFootball Implementation Status

## Current Master Phase
## Current Subphase
## Baseline / Inventory
## Completed
## Verified Existing Implementations
## In Progress
## Deferred
## Blocked
## Legacy Components Remaining
## Data Migrations
## Backfills
## Compatibility Routes / Contracts
## Canonical Owners Established
## Infrastructure Decisions
## Hosting / Deployment Status
## Media Storage / CDN Status
## Database / Cache / Broker Status
## Queue / Worker Capacity Status
## Backup / Restore / DR Status
## Observability / Alerts Status
## IaC / CI/CD Status
## Security / Privacy Risks
## Cost / Capacity Risks
## Tests / Quality Gates
## ADRs
## Known Risks
## Next Actions
```

Update it continuously as work progresses. Do not wait until the end of a long implementation run.

## A.8 Master execution order

The agent MUST execute in dependency order, not by whichever feature is easiest to add.

### Master Phase 0 — Repository baseline and characterization

- read this entire file;
- inspect git status, branches, local modifications, repository docs, settings, dependency files, apps/packages, migrations, APIs, models, tasks, events/signals, tests, media/storage paths, authentication, commercial logic, playback state, search/recommendations, community code, and football metadata;
- run safe baseline tests/checks;
- identify duplicate generations of functionality;
- record baseline in `SANFOOTBALL_IMPLEMENTATION_STATUS.md`;
- preserve high-risk current behaviour with characterization tests before migration.

### Master Phase 1 — Core canonicalisation and production-safe foundation

Execute the applicable Part I refactor phases. In parallel, obey Part II production-infrastructure constraints so the refactor does not create new local-disk, connection, queue, media-delivery, or deployment debt.

Required gate before feature expansion dependent on a domain:

- one canonical owner exists;
- duplicate mutable state is migrated or explicitly transitional;
- critical transitions are explicit and testable;
- database invariants exist where appropriate;
- permission/access policy is canonical;
- public compatibility is intentionally handled;
- tests establish the domain baseline;
- production deployment assumptions do not contradict Part II.

### Master Phase 2 — Production infrastructure foundation

Execute Part II Phase 0A and the detailed infrastructure mandates in Part II Sections 73–84. This phase may begin earlier for infrastructure needed by the refactor, but its acceptance gates MUST be satisfied before media-intensive growth features are considered production-ready.

### Master Phase 3 — Incremental feature programme

Execute Part II feature phases in dependency order, one reviewable increment at a time, using feature flags and safe migrations where needed.

### Master Phase 4 — Continuous hardening

Security, privacy, observability, performance, disaster recovery, cost control, dependency maintenance, documentation, and deletion of superseded code are continuous obligations rather than a final cleanup phase.

## A.9 Agent behaviour

When the user asks for implementation, the agent MUST implement rather than stop at a design description. For each scope:

```text
inspect → characterize → design → implement → migrate → test → document → observe → remove superseded code → report exact result
```

Do not create fake placeholders and declare a feature complete. Do not silently skip difficult portions. Do not hide unresolved architecture behind TODOs unless the work is explicitly deferred and recorded with rationale, risk, and dependency.

## A.10 Definition of success

The objective is not maximum feature count. The objective is a coherent, secure, fast, observable, highly scalable, cost-aware, production-grade football podcast/media platform in which:

```text
football event
    ↕
club / player / manager / competition / topic
    ↕
show / episode / chapter / moment / clip / live broadcast
    ↕
creator / network / community / listener
    ↕
subscription / membership / entitlement
    ↕
media / analytics / discovery / notifications / connected devices
```

can evolve without duplicate state or provider-specific architectural islands.

---

# PART I — CORE REFACTOR, CANONICALISATION, AND MODERNISATION

> This part contains the complete repository-consolidation mandate. It applies whenever the current repository has not yet satisfied a required canonicalisation rule. If a requirement is already correctly implemented, verify it rather than rebuilding it.

## AGENTS.md — SANFootball Architectural Consolidation and Production-Grade Refactoring Mandate

> **Repository:** `Leydotpy/sanfootball`  
> **Project:** SANFootball  
> **Product:** Football-focused podcast, sports-audio, discovery, community, membership, and premium-content platform  
> **Backend:** Django + Django REST Framework  
> **Background processing:** Celery  
> **Cache / broker:** Redis-compatible architecture  
> **Authentication:** Clerk-integrated identity with a local Django domain user  
> **Status:** **AUTHORITATIVE REFACTORING SPECIFICATION**

---

## 0. AUTHORITY, PURPOSE, AND SCOPE

This file is the governing specification for the consolidation, cleanup, modernization, hardening, migration, and staged refactoring of the SANFootball repository.

The repository has accumulated functionality over a long development lifetime. Many capabilities are useful, but several business concepts now exist in multiple generations or are represented by overlapping abstractions. The purpose of this refactor is **not** to reduce SANFootball to a small application. It is to preserve the valuable product while creating one canonical implementation for each important domain concept.

This specification therefore requires the implementation agent to:

1. preserve valuable product capability and user data;
2. identify one authoritative model/service for every important concept;
3. migrate callers and data to the authoritative implementation;
4. delete superseded implementations once migration is complete;
5. establish explicit bounded contexts and dependency rules;
6. strengthen correctness, security, performance, scalability, testability, observability, and documentation;
7. prevent the repository from accumulating a third generation of the same feature.

If current code conflicts with this file, this file wins unless an immediate change would produce irreversible data loss, an unresolved security issue, or an external compatibility break that cannot safely be migrated. In such cases, preserve data and active contracts temporarily, document the exception, and still converge on this specification.

The agent must distinguish four things:

- **product capability** — may need to be preserved;
- **public/client contract** — may require versioned compatibility;
- **stored data** — must be safely migrated or archived;
- **legacy implementation** — may and should be replaced.

“Backward compatibility” must never mean “keep broken architecture forever.”

---

## 1. EXECUTIVE MANDATE

SANFootball must emerge as a cohesive **football-focused podcast and sports-audio platform**, not a loose collection of Django apps.

The architecture must make these pillars obvious:

### 1.1 Content

- Podcast/show
- Season
- Episode
- Audio/media variants
- Chapters
- Transcripts
- Summaries
- Sports metadata

### 1.2 Listening

- Playback progress
- Continue listening
- Listening history
- Queue / Up Next
- Playlists
- Bookmarks
- Streaming
- Preview playback
- Downloads and eventual offline listening

### 1.3 Discovery

- Search
- Transcript search
- Trending
- Editorial rails
- Personalized recommendations
- Sports-entity discovery
- Team/player/competition feeds

### 1.4 Community

- Follows
- Reactions
- Comments
- Timestamp comments
- Polls
- Moderation

### 1.5 Commercial

- Plans
- Prices
- Paid subscriptions
- Entitlements
- Access policies
- Billing-provider integration
- Premium content
- Early access
- Private feeds/download rights when justified

The final repository must make it difficult to confuse one concept with another.

---

## 2. PRODUCT NORTH STAR

The architectural north star is:

> **SANFootball is the podcast and sports-audio platform built specifically for football fans.**

Do not design the backend merely as a generic Spotify clone.

The product must exploit football-specific structured metadata such as:

- clubs/teams;
- players;
- leagues;
- competitions;
- fixtures/matches;
- countries;
- regions;
- managers/coaches when modeled;
- topics such as transfers, tactics, injuries, previews, post-match analysis, and breaking news.

The target architecture must be capable of supporting experiences such as:

- Continue Listening
- New From Shows You Follow
- Because You Follow Arsenal
- Latest Victor Osimhen Mentions
- Premier League Analysis
- Today’s Matchday Audio
- Trending in Nigeria
- Editors’ Picks
- Premium Early Access
- Match Preview
- Post-Match Reaction
- Episodes Mentioning This Player
- Jump to the Moment This Player Was Discussed

The football graph is a strategic differentiator and must be strengthened, not abstracted away.

---

## 3. KNOWN TECHNICAL-DEBT CATEGORIES

The implementation agent must explicitly resolve the following categories rather than merely moving files.

### 3.1 Configuration debt

Current environment selection is not sufficiently explicit. Production and development settings must be deterministic and selected intentionally.

### 3.2 Dependency debt

The web runtime currently mixes core Django/API dependencies with media, scientific Python, ML, transcription, and worker-oriented dependencies. The refactor must isolate heavyweight workloads and reduce startup/runtime surface.

### 3.3 Membership/access debt

The repository has overlapping concepts around Plan, Feature, Membership, Subscription, Entitlement, AddOn, category-to-plan relationships, episode exclusivity, and early access. Duplicate state and stale service assumptions must be removed.

### 3.4 Queue/playback debt

Multiple ordering/state concepts coexist. The queue requires a canonical rewrite with one ordering model and explicit concurrency semantics.

### 3.5 Recommendation debt

Several recommendation generations exist. Only one recommendation architecture should survive. ML training must never happen at Django module import.

### 3.6 API-structure debt

Presentation-layer modules are too deeply nested and in places registered like independent Django apps. Feature code should become discoverable by domain.

### 3.7 Legacy framework debt

Oscar-derived dynamic loading/application wiring remains. Unless a demonstrated active requirement depends on application forking/overrides, it must be removed.

### 3.8 Community duplication

Generic comments and a separate forum/discussion implementation overlap. One canonical community discussion model must remain.

### 3.9 Offline complexity

The current custom offline packaging/licensing/cryptographic subsystem is disproportionately complex relative to the maturity of surrounding billing/access rules. Offline listening is valid; the current implementation is not sacred.

---

## 4. NON-NEGOTIABLE ENGINEERING PRINCIPLES

### 4.1 One concept, one source of truth

Examples:

- one authoritative subscription status;
- one access policy;
- one queue position;
- one podcast-follow concept;
- one playback-progress model;
- one recommendation service;
- one active billing-domain model;
- one listener-identity mapping.

Never retain two independently mutable fields that represent the same state.

### 4.2 Domain logic must not depend on presentation logic

Allowed:

```text
API/View -> Service/Policy/Selector -> Models
```

Forbidden:

```text
Domain Service -> DRF Serializer
Domain Model -> API View
Recommendation Service -> REST Serializer
```

Domain services return models, querysets, identifiers, score objects, or typed internal DTOs. APIs serialize them.

### 4.3 Critical transitions must be explicit

The following must be explicit service/use-case operations rather than hidden signal side effects:

- activate/cancel subscription;
- grant/revoke entitlement;
- process billing webhook;
- create/merge/reorder queue;
- authorize protected download;
- issue protected media access;
- perform important state transitions.

Signals may be used for secondary reactions such as safe cache invalidation, metrics, or non-critical notification hooks.

### 4.4 Database invariants belong in the database

Use:

- `UniqueConstraint`;
- `CheckConstraint`;
- conditional constraints;
- foreign keys;
- indexes;
- transactional locking.

Do not rely exclusively on application code to prevent impossible states.

### 4.5 Idempotency is mandatory where retries are normal

Especially:

- payment webhooks;
- media callbacks;
- subscription synchronization;
- entitlement grants;
- asynchronous processing requests;
- import jobs.

### 4.6 No speculative framework design

Do not build generalized systems for product ideas that do not currently exist.

Avoid premature:

- generic e-commerce;
- coaching/merchandise commerce;
- arbitrary event ticketing;
- multiple payment providers;
- multiple brokers;
- complex plugin frameworks;
- custom DRM expansion.

### 4.7 No dead commented-out implementation

Delete dead code after migration. Version control is the archive.

### 4.8 Important domain behavior must be testable without HTTP

Examples:

- evaluate access;
- move queue item;
- merge queue;
- cancel subscription;
- record progress;
- recommend episodes.

### 4.9 Preserve stable public identifiers where practical

Keep podcast/episode public IDs and slugs stable when possible. If routes change, provide an intentional migration/deprecation strategy.

### 4.10 Refactor through safe migrations

Use expand -> backfill -> switch -> verify -> contract. Destructive big-bang migration is forbidden for high-value data.

---

## 5. TARGET BOUNDED CONTEXTS

Converge toward:

```text
app/
├── config/
│   ├── settings/
│   ├── urls.py
│   ├── asgi.py
│   └── celery.py
│
├── apps/
│   ├── identity/
│   ├── sports/
│   ├── podcasts/
│   ├── media/
│   ├── playback/
│   ├── library/
│   ├── memberships/
│   ├── billing/
│   ├── discovery/
│   ├── community/
│   ├── analytics/
│   └── editorial/
│
└── common/
    ├── cache/
    ├── db/
    ├── events/
    ├── exceptions/
    ├── logging/
    ├── pagination/
    ├── storage/
    ├── typing/
    └── utils/
```

Do not create a Django app merely because a directory exists. A subpackage such as `media/transcription` does not automatically need separate app registration.

---

## 6. DOMAIN DEPENDENCY RULES

Preferred dependency direction:

```text
identity
sports
   ↑
podcasts
   ↑
media

identity + podcasts -> playback
identity + podcasts -> library
identity + podcasts -> memberships
memberships -> billing integration boundary
sports + podcasts + playback + library + analytics -> discovery
identity + podcasts -> community
discovery + editorial + playback -> home/API composition
```

Rules:

1. `billing` must not contain editorial content policy.
2. `memberships` owns entitlement/access evaluation.
3. `podcasts`, `analytics`, and `discovery` must not import DRF serializers.
4. `media` must call canonical access policy before protected delivery.
5. `sports` must not depend on commercial plan tiers.
6. `common` must contain genuinely reusable infrastructure only.
7. Circular imports are architectural smells; do not normalize them with indiscriminate local imports.

---

## 7. CANONICAL DOMAIN VOCABULARY

### Follow

A free listener relationship expressing interest in a podcast, team, player, or competition.

A follow is not a paid subscription.

### Plan

A SANFootball commercial tier defining capabilities.

### Price

A billable currency/interval price for a plan.

### Subscription

A recurring commercial contract between a user and a price/plan.

### Entitlement

A durable or temporary explicit grant allowing a user to access a resource/capability independently of normal plan evaluation.

### Access Policy

The authoritative evaluator deciding whether a subject may perform an action on a resource.

### Playback Progress

Persistent progress state for an episode.

### Queue / Up Next

Transient ordered playback intention.

### Playlist

Persistent curated collection.

### Bookmark

A saved timestamp/position, optionally with a note.

### Category / Topic

Editorial/discovery metadata. It must not be the commercial access-control mechanism.

---

## 8. TARGET PODCAST CONTENT MODEL

### 8.1 Podcast

Recommended fields:

```text
id
title
slug
subtitle
description
status
explicit_content
language
website_url
published_at
created_at
updated_at
```

Relationships may include:

```text
categories/topics
teams
players
competitions
countries
regions
```

Required behavior:

- published episode retrieval;
- season retrieval;
- follower count without serializing all followers;
- stable public slug;
- search metadata;
- deterministic artwork selection.

### 8.2 Season

Prefer an explicit Season model over representing a season as a child Podcast.

Recommended:

```text
id
podcast
number optional
title
description
position
published_at
```

Migrate existing parent/child Podcast season data safely. Do not delete legacy season data until episode mappings and client/API behavior are verified.

### 8.3 Episode

Recommended fields:

```text
id
podcast
season
title
slug
subtitle
description
episode_number
episode_type
status
published_at
premium_available_at
public_available_at
visibility
required_plan
preview_duration_seconds
explicit_content
duration_seconds
created_at
updated_at
```

Do not infer commercial access from category membership.

Suggested visibility semantics:

```text
PUBLIC
MEMBERS
PLAN
ENTITLEMENT
```

Release timing should distinguish premium availability from public availability rather than deriving everything indirectly.

---

## 9. SPORTS METADATA

Preserve structured relationships between content and:

- countries;
- regions;
- competitions;
- leagues;
- clubs/teams;
- players;
- matches;
- managers/coaches where useful.

Do not flatten all football knowledge into generic strings/tags.

The architecture should later support followable sports entities and transcript-linked entity mentions.

Potential future model:

```text
EpisodeEntityMention
    episode
    entity_type
    entity_id
    start_seconds
    end_seconds
    confidence
    source
```

This enables timestamp search, entity feeds, recommendations, and player/team mention pages.

---

## 10. MEDIA ARCHITECTURE

Separate:

1. source/master media;
2. processed variants;
3. protected delivery;
4. transcription;
5. chapters/derived metadata;
6. download authorization.

### 10.1 Replace overloaded audio quality

`HLS` and `PREVIEW` are not qualities.

Use an AudioAsset/AudioVariant model such as:

```text
id
episode
role
delivery_format
codec
bitrate_kbps
sample_rate_hz
duration_seconds
size_bytes
file/storage_key
processing_status
is_primary
created_at
```

Suggested roles:

```text
MASTER
RENDITION
PREVIEW
```

Suggested formats:

```text
MP3
AAC
HLS
```

Quality may be represented by preset or bitrate.

### 10.2 Streaming authorization

Protected stream flow:

1. resolve episode;
2. evaluate canonical AccessPolicy for `STREAM`;
3. determine full vs preview;
4. select variant;
5. issue short-lived signed URL/CDN credential;
6. record metrics;
7. never return permanent private-storage URLs.

Metadata visibility is not media authorization.

### 10.3 HLS

Protected HLS manifests/segments must remain private behind signed cookies, signed URLs, or equivalent CDN authorization.

### 10.4 Processing

FFmpeg/transcoding must run asynchronously. Track job ID, status, attempts, timestamps, errors, input, and output.

### 10.5 Selected Cloudflare media implementation through `pycflare`

The current production implementation MUST use Cloudflare through the Python package maintained at:

```text
https://github.com/Leydotpy/pycflare
```

The Cloudflare product boundary is intentional:

```text
Audio / arbitrary binary objects / source files / waveforms / captions
    -> Cloudflare R2 through pycflare R2/Django storage interfaces

User-facing artwork / photographs / image variants / private images
    -> Cloudflare Images through pycflare ImagesClient/AsyncImagesClient

Video podcast upload / encoding / adaptive playback / private video
    -> Cloudflare Stream through pycflare StreamClient/AsyncStreamClient
```

The domain model MUST remain provider-neutral, but the concrete production adapters MUST be Cloudflare-backed until a later ADR explicitly changes provider.

Rules:

1. Django/Python code MUST NOT add a parallel direct `boto3`, raw Cloudflare REST, or unrelated Cloudflare SDK implementation for capabilities already exposed by `pycflare`.
2. Public R2 delivery MUST use a production custom domain/edge path rather than `r2.dev`.
3. Protected R2 objects MUST be issued through short-lived capabilities generated by the backend; permanent private object URLs MUST NOT be persisted in API responses.
4. Cloudflare Images used for gated/private artwork MUST be created with signed delivery required and signed server-side through the `pycflare` Images signing surface.
5. Cloudflare Stream videos that are private, premium, early-access, members-only, or otherwise gated MUST require signed playback.
6. Provider upload URLs, signing keys, API tokens, R2 secrets, Stream credentials, and Images signing material are bearer secrets and MUST never be logged or stored in ordinary model fields.
7. Provider IDs belong in provider-facing asset/location metadata only; episode, show, entitlement, and playback business logic MUST use canonical SANFootball identifiers.

---

## 11. TRANSCRIPTION, CHAPTERS, SUMMARIES, AND AI

These capabilities are strategically valuable and should remain.

### 11.1 Transcript

Canonical transcript data should include:

```text
episode
language
provider
model/version
full_text
segments
audio_duration_seconds
cost
status
created_at
updated_at
srt_file optional
vtt_file optional
```

Segments must preserve timestamps.

### 11.2 Transcript search

The architecture must later support:

```text
episode
matched snippet
start_seconds
entity/topic
```

so search can jump directly to spoken moments.

### 11.3 Chapters

Keep chapters.

Recommended fields:

```text
episode
title
start_seconds
end_seconds
description
image optional
source
confidence optional
position
```

Sources:

```text
MANUAL
AI_GENERATED
IMPORTED
```

### 11.4 Summary provenance

Store provider/model/prompt version so summaries remain auditable.

### 11.5 Configuration ownership

Listener preferences must not choose server transcription providers. Server content-processing policy belongs in server/domain configuration.

---

## 12. PLAYBACK DOMAIN

Playback must become a dedicated domain.

### 12.1 PlaybackProgress

Recommended:

```text
user
episode
progress_seconds
duration_seconds_at_last_update
started_at
last_played_at
completed_at
is_completed
play_count
last_device_id optional
updated_at
```

Constraint:

```text
unique(user, episode)
```

### 12.2 Completion

Do not trust a client-supplied completion Boolean blindly. Apply a defined threshold or verified end event.

### 12.3 Write efficiency

Do not persist playback every second. Use sensible checkpoints: periodic, pause, seek, close where reliable, and completion.

### 12.4 Continue Listening

One canonical selector must return incomplete recently played episodes. No endpoint may independently reinvent the logic.

---

## 13. QUEUE / UP NEXT — FULL REWRITE

The capability remains; the legacy implementation should be replaced.

Recommended models:

```text
PlaybackQueue
    id
    owner nullable
    session_key nullable
    device_id nullable
    created_at
    updated_at
    last_activity_at

QueueItem
    id
    queue
    episode
    position
    added_at
```

There must be one ordering field.

Required constraints:

```text
owner OR anonymous session identity required
unique(queue, episode)
unique(queue, position)
```

Create a QueueService with:

```text
get_or_create_for_request
add_last
play_next
play_now
move
remove
clear
replace
merge_anonymous_queue
```

Use transactions and `select_for_update()` where concurrent mutation can corrupt ordering.

Anonymous merge must be deterministic, atomic, duplicate-free, and tested.

---

## 14. LIBRARY DOMAIN

### 14.1 PodcastFollow

Replace free “subscription” vocabulary with follow vocabulary.

Recommended:

```text
user
podcast
followed_at
notifications_enabled
auto_download
```

Constraint:

```text
unique(user, podcast)
```

### 14.2 Sports follows

Support later:

- TeamFollow
- PlayerFollow
- CompetitionFollow

or a carefully designed typed follow abstraction.

### 14.3 Playlist

Keep playlists separate from queue.

Recommended:

```text
Playlist
    id
    user nullable for editorial
    name
    description
    slug
    type
    visibility
    created_at
    updated_at

PlaylistItem
    playlist
    episode
    position
    added_at
```

Only one position field.

### 14.4 Bookmark

Add after core consolidation:

```text
user
episode
position_seconds
note
created_at
updated_at
```

Bookmarks are distinct from playback progress.


---

## 15. MEMBERSHIP, PLAN, PRICE, SUBSCRIPTION, AND ENTITLEMENT REDESIGN

This is one of the highest-priority domains.

### 15.1 Plan

A Plan defines product capabilities, not prices.

Recommended:

```text
id
code
name
description
rank
is_active
created_at
updated_at
```

`code` must be stable and unique.

Example:

```text
free
fan
pro
insider
```

Never use a display name as the durable provider/integration identifier.

### 15.2 Feature / Capability

Stable feature codes may include:

```text
premium_audio
early_access
offline_download
high_quality_audio
transcripts
private_rss
live_qna
vip_events
```

Do not let a generic Feature model become a sparse table with many fields applicable to only one feature. If configuration becomes substantial, use explicit policy/configuration models or a validated configuration object.

### 15.3 Price

Price is separate from Plan.

Recommended:

```text
id
plan
code
currency
amount
billing_interval
provider
provider_product_id optional
provider_price_id
is_active
created_at
updated_at
```

Intervals:

```text
MONTH
YEAR
```

Do not retain fixed `price_monthly` and `price_annual` columns as the long-term pricing architecture.

A Plan may have:

```text
Fan Monthly NGN
Fan Annual NGN
Fan Monthly USD
```

without duplicating the Plan.

### 15.4 Subscription

A Subscription must have exactly one authoritative status.

Recommended:

```text
id
user
price
provider
provider_customer_id
provider_subscription_id
status
current_period_start
current_period_end
trial_end
cancel_at_period_end
canceled_at
ended_at
created_at
updated_at
```

Recommended states:

```text
TRIALING
ACTIVE
PAST_DUE
PAUSED
CANCELED
EXPIRED
```

Do not keep a second mutable `active` Boolean.

Expose derived semantics:

```text
grants_access
is_current
is_renewing
```

### 15.5 Membership wrapper

Evaluate whether the current separate Membership model has independent business meaning.

If it only wraps `User` and a plan/subscription, migrate away from it.

Do not keep models merely because historical code expects them.

### 15.6 Entitlement

Entitlements are explicit grants.

Recommended semantics:

```text
id
user
resource_type/capability
resource_id optional
source_type
source_id
valid_from
valid_until
revoked_at
revoked_reason
metadata
created_at
```

If Django ContentTypes remain, the service must always evaluate the actual resource object correctly.

Prefer historical grant rows over one forever-mutated row when auditability matters.

Possible sources:

```text
SUBSCRIPTION
ADMIN
GIFT
PROMOTION
PURCHASE
MIGRATION
```

### 15.7 AddOn

Remove the generic existing AddOn concept unless there is a live product requirement.

Do not keep speculative:

- coaching sessions;
- merchandise vouchers;
- generic credits;
- arbitrary event products.

If single-episode purchases are later required, design that requirement deliberately.

---

## 16. CANONICAL ACCESS POLICY

There must be one authoritative access evaluator.

Suggested interface:

```python
decision = access_policy.evaluate(
    user=user,
    resource=episode,
    action=AccessAction.STREAM,
    now=now,
)
```

### 16.1 Actions

At minimum:

```text
VIEW_METADATA
STREAM
DOWNLOAD
VIEW_TRANSCRIPT
COMMENT
EARLY_ACCESS
```

Future:

```text
PRIVATE_RSS
JOIN_LIVE
VIEW_VIDEO
```

### 16.2 AccessDecision

Internally, do not reduce every decision to a Boolean.

Recommended:

```text
allowed
reason
required_plan
preview_allowed
effective_subscription
effective_entitlement
expires_at optional
```

Possible reason codes:

```text
PUBLIC
STAFF_BYPASS
ACTIVE_PLAN
ENTITLEMENT
EARLY_ACCESS
REQUIRES_LOGIN
REQUIRES_PLAN
NOT_YET_RELEASED
EXPIRED
REVOKED
```

### 16.3 Evaluation order

Use a documented deterministic order:

1. validate resource publication/status;
2. intentional staff bypass if enabled;
3. public rule;
4. authentication requirement;
5. direct valid entitlement;
6. active subscription/plan capability;
7. early-access window;
8. deny with structured reason;
9. evaluate preview separately when appropriate.

Do not scatter access logic among:

- model methods;
- serializers;
- stream views;
- download views;
- offline endpoints;
- frontend logic.

### 16.4 Caching

Access decisions may be cached briefly.

Requirements:

- cache key includes user, resource, action, and policy version;
- short TTL;
- subscription/entitlement updates invalidate user authorization cache;
- cache failure must never grant access;
- cache is not authoritative commercial state.

### 16.5 Mandatory access test matrix

At minimum:

```text
anonymous + public
anonymous + premium
free user + public
free user + premium
fan + fan
fan + pro
pro + fan
trialing
past due
cancel-at-period-end before expiry
canceled after expiry
expired
direct entitlement
expired entitlement
revoked entitlement
staff bypass
before early-access window
inside early-access window
after public release
preview allowed
preview unavailable
download allowed/denied
transcript allowed/denied
```

No protected-media endpoint may bypass this policy.

---

## 17. BILLING ARCHITECTURE

Billing must become a small external-provider integration domain rather than a generalized e-commerce framework.

### 17.1 Minimize PCI scope

SANFootball should normally **not** collect/store raw card numbers or CVVs.

Use provider-hosted or provider-tokenized payment flows.

Remove legacy bank-card forms/models unless there is a formally reviewed requirement to retain them.

### 17.2 Local billing data

Possible canonical records:

```text
BillingCustomer
Payment
Invoice
WebhookEvent
```

Only persist provider concepts that have local operational/business value.

### 17.3 Provider interface

Use a small interface, for example:

```python
class BillingProvider(Protocol):
    def create_checkout_session(...): ...
    def cancel_subscription(...): ...
    def change_subscription(...): ...
    def verify_webhook(...): ...
    def parse_event(...): ...
```

Do not create a large plugin framework.

Implement the provider(s) actually used.

### 17.4 WebhookEvent

Mandatory fields:

```text
provider
external_event_id
event_type
payload_hash
received_at
processed_at
status
attempt_count
last_error
```

Constraint:

```text
unique(provider, external_event_id)
```

Webhook processing must be idempotent.

### 17.5 Provider/domain separation

Provider-specific statuses must be mapped at the integration boundary.

Application code outside billing/membership must not depend directly on Stripe/Paystack/etc. status strings.

### 17.6 Cancellation

Define and test:

- cancel now;
- cancel at period end;
- paid-through period;
- retry/grace behavior;
- expiration;
- reactivation.

### 17.7 Refunds/chargebacks

Define local subscription/entitlement consequences and ensure they are replay-safe.

---

## 18. COMMUNITY ARCHITECTURE

### 18.1 Canonical discussion system

Use the generic comments/replies direction as the canonical system.

The legacy forum/discussion implementation should be removed after caller/data verification unless a genuinely separate forum product requirement exists.

### 18.2 Comment

Recommended:

```text
id
user
target/content object
parent nullable
body
timestamp_seconds optional
status
created_at
updated_at
```

If comment media remains supported, validate uploads and consider a separate attachment model if complexity grows.

### 18.3 Timestamp comments

A football podcast benefits from comments tied to moments:

```text
42:16 — That penalty decision was ridiculous.
```

`timestamp_seconds` should eventually allow one-click playback navigation.

### 18.4 Reactions

If one reaction per user/resource is the intended rule, enforce a database uniqueness constraint and update the reaction instead of accumulating duplicates.

### 18.5 Polls

Polls are a valid future sports-engagement feature.

Targets may include:

- episode;
- match;
- podcast;
- editorial module.

Examples:

- Man of the Match?
- Was that a penalty?
- Who should Arsenal sign?
- Score prediction?

### 18.6 Moderation

Before increasing UGC scope, support:

```text
report
hide/remove
moderation status
rate limits
audit information
```

Do not create an unmoderated social layer.

---

## 19. DISCOVERY AND RECOMMENDATION

Only one recommendation architecture should survive.

### 19.1 Remove legacy experiments

Delete old TensorFlow/TensorFlow-Datasets recommendation code after confirming there are no active callers.

### 19.2 Baseline recommendation signals

Prefer explainable signals before advanced ML:

- followed podcasts;
- followed teams;
- followed players;
- followed competitions;
- playback starts;
- completions;
- abandonment/skips where reliable;
- recency;
- reactions;
- search interactions;
- episode trending;
- sports/topic taxonomy;
- editorial boosts.

### 19.3 Recommendation output

Domain recommendation should return a typed structure such as:

```text
Recommendation
    resource_id
    score
    reason_code
    reason_context
```

Reason examples:

```text
FOLLOWED_PODCAST
FOLLOWED_TEAM
FOLLOWED_PLAYER
SIMILAR_TOPIC
TRENDING
CONTINUE_LISTENING
EDITORIAL
```

### 19.4 Home feed

Introduce a `HomeFeedService`.

Possible rails:

```text
Continue Listening
New From Followed Shows
Your Teams
Your Players
Matchday
Recommended For You
Trending
Editors' Picks
Premium
Recently Added
```

Do not serialize rich episode-detail objects into home rails.

### 19.5 Advanced ML

If ML is later justified:

- training runs in a management command or background/ML worker;
- artifacts are versioned;
- training metadata is retained;
- fallback recommendations exist;
- web startup never trains a model;
- heavy ML libraries do not need to exist in the web image.

### 19.6 Cold start

New-user fallbacks may use:

- onboarding interests;
- followed sports entities;
- followed shows;
- trending;
- editorial;
- consented location context if product-relevant.

---

## 20. SEARCH

Search should ultimately cover:

- podcast title;
- episode title;
- descriptions;
- tags/topics;
- teams;
- players;
- competitions;
- matches;
- transcripts.

Start with PostgreSQL full-text/search capabilities if sufficient.

Do not introduce Elasticsearch/OpenSearch without a measured need.

Transcript results should support direct time offsets.

---

## 21. ANALYTICS AND DOMAIN EVENTS

### 21.1 Separate state from event history

`PlaybackProgress` is current state.

“Episode started” is an event.

Do not conflate them accidentally.

### 21.2 Event vocabulary

Potential events:

```text
CONTENT_IMPRESSION
PODCAST_OPENED
EPISODE_STARTED
EPISODE_PROGRESS
EPISODE_COMPLETED
EPISODE_SKIPPED
PODCAST_FOLLOWED
PODCAST_UNFOLLOWED
QUEUE_ITEM_ADDED
QUEUE_ITEM_REMOVED
PLAYLIST_ITEM_ADDED
SEARCH_PERFORMED
SEARCH_RESULT_OPENED
COMMENT_CREATED
REACTION_CHANGED
PAYWALL_VIEWED
PREVIEW_STARTED
SUBSCRIPTION_CHECKOUT_STARTED
SUBSCRIPTION_ACTIVATED
```

### 21.3 Transactional publication

For events caused by database transitions, use `transaction.on_commit()` or a transactional outbox.

Never publish a critical event before its state transaction commits.

### 21.4 Broker posture

Do not introduce Kafka during this refactor.

Celery/Redis and a database outbox are adequate initially.

### 21.5 Privacy

Define retention/anonymization for IP-based anonymous analytics.

Do not retain raw IPs indefinitely by default.

---

## 22. EDITORIAL / PROMOTIONS

The product needs editorial curation, not an inherited generic promotion framework.

Recommended simplified model:

```text
HomeRail
    id
    code
    title
    subtitle
    type
    algorithm
    position
    active_from
    active_until
    is_active
    config

HomeRailItem
    rail
    content_type
    object_id
    position
```

Optional:

```text
CampaignBanner
```

Suggested rail types:

```text
EDITORIAL
TRENDING
LATEST
FOLLOWING
RECOMMENDED
TEAM
PLAYER
COMPETITION
PREMIUM
CONTINUE_LISTENING
```

If remote banner rendering is actively valuable, isolate it as an integration. If unused, remove it.

Do not let banner-rendering infrastructure define the home-feed domain.

---

## 23. OFFLINE / DOWNLOAD STRATEGY

Offline listening remains a valid product capability.

The existing custom DRM implementation must be treated as replaceable.

### 23.1 Immediate posture

Feature-flag or disable the risky/custom DRM flow until:

- AccessPolicy is canonical;
- billing/subscription status is canonical;
- download entitlement is reliable;
- client requirements are known;
- cryptographic design can be reviewed.

### 23.2 Interim downloads

Where product requirements allow:

1. evaluate `DOWNLOAD`;
2. issue a short-lived signed object URL;
3. enforce plan/device policy at issuance;
4. let the client store content using its protected local mechanisms.

### 23.3 Future DRM

If native DRM becomes justified, implement a dedicated subsystem with:

- canonical AccessPolicy;
- device identity;
- license expiry;
- revocation;
- proper key management;
- abuse/replay considerations;
- professional cryptographic review.

Do not casually expand a custom encryption container.

---

## 24. AUTHENTICATION AND IDENTITY

Choose a coherent source of authentication.

If Clerk remains:

```text
Clerk Identity
    ->
Identity Mapping
    ->
Django User / domain identity
```

Store the external Clerk ID in a stable unique mapping.

### 24.1 DRF

Every endpoint must have explicit expected authentication behavior.

Do not accidentally mix session and bearer authentication across endpoints.

### 24.2 Authorization

Clerk authentication answers identity.

SANFootball domain permissions and entitlements answer authorization.

Do not let client claims bypass AccessPolicy.

### 24.3 Staff/admin

Use coherent Django groups/permissions or equivalent role mapping.

Avoid a proliferation of hardcoded job-title permission classes unless business roles truly require them.

---

## 25. API ARCHITECTURE

### 25.1 Flatten the API hierarchy

Prefer feature-local APIs:

```text
apps/podcasts/api/public/
apps/podcasts/api/admin/
apps/playback/api/public/
apps/memberships/api/public/
```

or an equivalent clear structure.

Do not create numerous registered Django apps just for serializers/views/URL wiring.

### 25.2 Versioning

Prefer stable routes such as:

```text
/api/v1/
```

If old clients exist, introduce compatibility/deprecation intentionally.

### 25.3 Serializer tiers

Examples:

```text
PodcastCardSerializer
PodcastDetailSerializer
EpisodeCardSerializer
EpisodePlayerSerializer
EpisodeDetailSerializer
EpisodeAdminSerializer
```

Never use one giant serializer everywhere.

### 25.4 Bound collections

Do not embed all comments, reactions, followers, or related resources in an episode detail response.

Provide:

```text
comment_count
reaction_summary
followers_count
```

and paginated endpoints.

### 25.5 Error contract

Use a stable structured error response.

Example:

```json
{
  "error": {
    "code": "subscription_required",
    "message": "This episode requires a Pro subscription.",
    "details": {
      "required_plan": "pro"
    }
  }
}
```

Do not leak raw exceptions.

### 25.6 OpenAPI

Keep generated API schema valid in CI.

---

## 26. HOME-FEED PERFORMANCE

Build the home feed through a composition service:

1. resolve enabled rail definitions;
2. obtain data from selectors/recommenders;
3. prefetch related podcast/artwork/progress;
4. serialize lightweight cards;
5. cache expensive public rails;
6. keep personalized caching short-lived and invalidatable.

The home feed must not cause hundreds of SQL queries.

---

## 27. DATABASE / ORM REQUIREMENTS

### 27.1 PostgreSQL-first design

Use PostgreSQL capabilities intentionally.

### 27.2 Selectors

Create reusable read paths such as:

```text
get_continue_listening(user)
get_followed_podcast_updates(user)
get_episode_for_playback(...)
get_trending_episodes(...)
```

### 27.3 N+1 prevention

Use:

- `select_related`;
- `prefetch_related`;
- filtered Prefetch;
- annotations;
- aggregates.

High-traffic endpoints require query-count regression tests.

### 27.4 Aggregate in the database

Do not materialize all episodes merely to calculate counts/durations when a SQL aggregate is appropriate.

### 27.5 Indexes

Index real query predicates such as:

- subscription lookup;
- publication/release;
- queue order;
- playback history;
- follow lookup;
- analytics timestamps;
- search/recommendation access paths.

Avoid speculative index proliferation.

### 27.6 Generic relations

Generic relations may remain for flexible concepts such as reactions/comments/entitlements, but must have normalized object IDs and `(content_type, object_id)` indexes.

Do not use GenericForeignKey to avoid modeling obvious core relationships.

---

## 28. CACHE REQUIREMENTS

Redis may be used for:

- short access-decision caching;
- recommendation payloads;
- public home rails;
- rate limiting;
- Celery;
- ephemeral processing state.

Rules:

1. cache is never authoritative commercial state;
2. cache miss must be correct;
3. cache outage must not grant premium access;
4. keys are namespaced/versioned;
5. sensitive authorization invalidation is explicit;
6. avoid unsafe wildcard scans at scale.

---

## 29. CELERY AND BACKGROUND TASKS

Use Celery for:

- transcription;
- media processing;
- summaries;
- recommendation recalculation;
- search indexing if introduced;
- webhook follow-up;
- notifications;
- cleanup;
- analytics aggregation.

Every task must:

- be retry-safe or explicitly document why not;
- use bounded retries/backoff;
- have structured logging;
- record failure;
- avoid unnecessary large in-memory datasets;
- use transactions deliberately;
- not depend on request objects.

Separate queues where useful:

```text
default
media
transcription
ml
```

Slow media work must not starve billing or ordinary tasks.

Model training is never an import side effect.

---

## 30. DEPENDENCY AND DEPLOYMENT ARCHITECTURE

Split dependencies conceptually into:

```text
core web
media
transcription
ml
development/test
```

Use optional dependency groups and/or separate worker images.

The web process should not import Torch/FAISS merely to return podcast JSON.

Remove duplicate/incorrect declarations.

Use reproducible builds.

If Python 3.14+ remains the target, verify real dependency compatibility and document the supported runtime matrix.

---

## 31. SETTINGS REFACTOR — PHASE 0

Replace implicit settings composition with explicit modules:

```text
config/settings/
    base.py
    development.py
    test.py
    production.py
```

Use `DJANGO_SETTINGS_MODULE`.

### Production

Must include:

- `DEBUG=False`;
- explicit allowed hosts;
- secure cookies;
- HTTPS redirect where appropriate;
- HSTS after verified deployment;
- proxy SSL configuration;
- explicit CORS/CSRF origins;
- environment-sourced secrets;
- explicit database;
- explicit storage;
- explicit Celery.

### Development

May use debug/local infrastructure.

Create `.env.example` with placeholders and explanations, never real secrets.

---

## 32. SECURITY REQUIREMENTS

Security improvements are part of the refactor.

### 32.1 Protected media

Authorize at delivery time.

### 32.2 Payments

Do not store CVV. Avoid raw PAN storage. Prefer hosted/tokenized providers.

### 32.3 Webhooks

Verify signatures and prevent replay/duplicate processing.

### 32.4 Rate limits

Apply reasonable throttles to:

- sensitive auth routes;
- comments/reactions;
- search;
- expensive recommendation endpoints;
- stream-token issuance;
- download authorization;
- device registration if retained.

### 32.5 Upload validation

Validate:

- size;
- extension;
- detected MIME type;
- codecs;
- filenames.

Do not trust client MIME declarations.

### 32.6 FFmpeg

Use argument-safe subprocess execution, no shell injection, timeouts/resource limits where practical, and reliable temporary cleanup.

### 32.7 SSRF

Protect any server-side URL fetch/callback/import path from access to internal network targets.

### 32.8 Secrets

Do not place credentials/private keys/tokens in Git, logs, exceptions, API output, or docs.

### 32.9 Logging redaction

Never log passwords, auth tokens, payment secrets, private keys, or unredacted highly sensitive webhook data.

### 32.10 Dependency audit

CI must include a suitable Python dependency/security audit.


---

## 33. OBSERVABILITY

Production-grade behavior must be observable.

### 33.1 Structured logging

Use structured fields where relevant:

```text
request_id
correlation_id
user_id
episode_id
podcast_id
task_id
provider
event_id
duration_ms
status
error_code
```

Avoid both extremes:

- cryptic one-word logs;
- massive unstructured prose for routine events.

### 33.2 Correlation

Generate or honor a request ID and propagate correlation context into Celery tasks where practical.

### 33.3 Metrics

Expose meaningful metrics for:

```text
HTTP latency/status
database errors
Celery task duration/failure
stream authorization granted/denied
signed URL issuance
playback progress writes
queue mutation latency
billing webhook processing
subscription transitions
transcription duration/cost/failure
media processing failure
recommendation latency
recommendation cache hit rate
```

### 33.4 Health

Provide:

```text
/health/live
/health/ready
```

Liveness should be lightweight.

Readiness may verify critical dependencies conservatively.

Do not make liveness fail because an optional third-party integration is unavailable.

---

## 34. PERFORMANCE REQUIREMENTS

Performance must be measured.

Initial targets under representative conditions may be:

```text
normal API p95               <= 250 ms where feasible
queue mutation p95           <= 150 ms excluding client network
cached access decision p95   <= 30 ms
stream credential issue p95  <= 150 ms excluding CDN/provider latency
home feed p95                <= 400 ms with sensible caching
```

These are engineering targets, not contractual promises.

If a target is not feasible, document measurements and bottleneck.

### 34.1 Query budgets

High-traffic endpoints require bounded query counts.

The query count must grow with logical sections, not with the number of returned items.

### 34.2 Repeated serializer queries

Eliminate SerializerMethodField patterns that issue one query per object where prefetching/annotation can solve the problem.

### 34.3 Denormalization

Use denormalized values such as trend score or counters only if:

- ownership is clear;
- update semantics are defined;
- eventual consistency is acceptable;
- a recompute/repair path exists.

---

## 35. TESTING MANDATE

No major phase is complete without tests.

### 35.1 Test layers

Maintain:

1. unit tests;
2. domain/service tests;
3. ORM/integration tests;
4. API contract tests;
5. migration tests;
6. security regression tests;
7. selected performance/query-count tests.

### 35.2 Highest-priority coverage

Especially strong behavioral coverage is mandatory for:

```text
AccessPolicy
Subscription
Entitlement
billing webhooks
stream authorization
download authorization
queue operations/merge
```

Coverage percentage is secondary to exhaustive important behavior.

### 35.3 Migration tests

For replaced models:

1. create representative legacy fixtures;
2. run migration/backfill;
3. verify target rows;
4. verify no loss;
5. verify compatibility behavior.

### 35.4 Queue tests

At minimum:

```text
add last
play next
play now
move
remove
clear
duplicate prevention
anonymous -> authenticated merge
two concurrent inserts
concurrent reorder
```

### 35.5 Access tests

Use the matrix in the AccessPolicy section.

### 35.6 Billing tests

At minimum:

```text
duplicate webhook
out-of-order webhook
trial -> active
renewal
failed payment
past due
cancel at period end
expiry
upgrade
downgrade
refund
chargeback if supported
```

### 35.7 Streaming tests

Verify:

- public full stream;
- premium denial;
- preview fallback;
- signed URL TTL;
- no full URL on denial;
- protected HLS denial when preview-only;
- download authorization independent of stream authorization.

---

## 36. MIGRATION PROTOCOL

Major model changes must use safe expand/migrate/contract steps.

### Step A — Expand

Add new schema without immediately deleting old schema.

### Step B — Backfill

Use deterministic data migrations or chunked/resumable management commands.

Large datasets should not be forced through one enormous migration transaction.

### Step C — Compatibility

Temporarily dual-read/write only when necessary.

Dual-write is transitional, not permanent.

### Step D — Switch

Move reads/writes to canonical implementation.

### Step E — Verify

Run:

- integrity/reconciliation scripts;
- tests;
- production metrics where applicable.

### Step F — Contract

Delete old code and later remove obsolete columns/tables.

Do not destroy high-value data in the same release that first introduces a replacement unless risk is demonstrably low.

---

## 37. INITIAL LEGACY-TO-TARGET MIGRATION MAP

The agent must maintain a living mapping.

Initial direction:

```text
apps.posts.podcasts.Podcast
    -> canonical podcasts.Podcast

child Podcast used as season
    -> podcasts.Season

apps.posts.podcasts.Episode
    -> podcasts.Episode

apps.posts.podcasts.PlayBack
    -> playback.PlaybackProgress

apps.queue.Queue
    -> playback.PlaybackQueue

apps.queue.QueueItem
    -> playback.QueueItem

apps.media.PlayList
    -> library.Playlist

apps.media.PlaylistItem
    -> library.PlaylistItem

AbstractAnalytics.subscribers
    -> library.PodcastFollow / explicit follow relationship

memberships.Plan
    -> canonical memberships.Plan

Plan price_monthly / price_annual
    -> Price records

memberships.Subscription
    -> canonical Subscription

memberships.Membership
    -> remove unless independent business meaning is demonstrated

memberships.Entitlement
    -> canonical Entitlement

memberships.AddOn
    -> remove unless actively required

apps.forum
    -> remove; migrate meaningful content if necessary

apps.posts.recommender
    -> remove

apps.recommendation
    -> retain concept, refactor into discovery recommendation domain

core.application / core.loading Oscar-style mechanisms
    -> remove after all callers migrate

apps.promotions
    -> editorial HomeRail/Campaign abstraction

media.offline custom DRM
    -> feature-flag/deprecate; preserve existing data until explicit cleanup
```

The exact implementation may adjust names to preserve Django app labels/migrations safely.

---

## 38. CODE ORGANIZATION INSIDE DOMAINS

A mature domain may contain:

```text
models/
selectors.py
services.py
policies.py
tasks.py
events.py
admin.py
api/
tests/
```

Do not mechanically create every file for every domain.

### Models

State and simple invariants.

### Selectors

Reusable query/read composition.

### Services

Transactional use cases and state transitions.

### Policies

Business/authorization decisions.

### Tasks

Asynchronous orchestration.

### API

HTTP concerns.

---

## 39. MODEL METHOD RULES

Appropriate model methods:

- simple predicates;
- local state helpers;
- small invariant-preserving operations.

Inappropriate:

- external provider calls;
- HTTP requests;
- large recommendation pipelines;
- API serialization;
- critical Celery dispatch hidden inside `save()`;
- complex commercial orchestration.

Avoid significant workflow logic in model `save()` overrides.

---

## 40. SIGNAL RULES

Signals are permitted but constrained.

Good:

- safe cache invalidation;
- metrics;
- non-critical derived updates.

Bad:

- charging a user;
- creating provider subscriptions;
- granting paid access as the only critical path;
- merging queues;
- processing provider webhooks;
- deleting protected media.

Never hide critical failures with:

```python
except Exception:
    pass
```

Expected failures should use typed exceptions and structured logging.

---

## 41. DOCUMENTATION REQUIREMENTS

The codebase must become understandable to another engineer.

Create and maintain:

```text
README.md
docs/
    architecture.md
    architecture-current.md
    domains.md
    access-control.md
    billing.md
    media.md
    playback.md
    queue.md
    recommendations.md
    deployment.md
    operations.md
    migrations.md
    security.md
    testing.md
    adr/
```

### 41.1 ADRs

Use Architecture Decision Records for major choices such as:

- explicit Season model;
- Plan/Price separation;
- canonical AccessPolicy;
- billing provider;
- removal of Oscar loading;
- offline DRM deprecation;
- recommendation architecture.

### 41.2 Code documentation

Public services, policies, complex selectors, and non-obvious algorithms require meaningful docstrings.

Document:

- purpose;
- parameters;
- invariants;
- side effects;
- transaction boundary;
- concurrency behavior;
- expected exceptions.

Do not fill files with docstrings that merely repeat names.

### 41.3 Diagrams

Use Mermaid where useful for architecture, data flows, and state transitions.

---

## 42. CI/CD REQUIREMENTS

Create a real CI pipeline.

At minimum:

```text
install
ruff lint
format check
mypy where practical
django system check
makemigrations --check
test suite
coverage
OpenAPI schema generation
dependency/security audit
```

CI must fail when model changes require uncommitted migrations.

Use explicit test settings.

Verify the production image/settings path starts successfully.

---

## 43. STYLE AND QUALITY STANDARDS

### 43.1 Python

Use modern typed Python compatible with the supported runtime.

### 43.2 Lint/format

Prefer a coherent Ruff-based toolchain where appropriate.

### 43.3 Typing

Strongly type:

- public service APIs;
- policies;
- DTOs;
- non-trivial helpers.

Do not add knowingly false annotations just to silence a checker.

### 43.4 Naming

Prefer domain language:

```text
PodcastFollow
PlaybackProgress
AccessDecision
BillingProvider
HomeRail
```

Avoid ambiguous names such as `Manager2`, `Handler`, `Engine`, or `Utils` where a domain-specific name is possible.

### 43.5 Exceptions

Use domain exceptions for expected business failures, for example:

```text
AccessDenied
SubscriptionRequired
QueueConflict
InvalidQueueOperation
BillingEventError
MediaUnavailable
```

Do not use generic `Exception` for ordinary business conditions.

---

## 44. API SECURITY AND PRIVACY

### 44.1 Follower identities

Do not expose full lists of podcast followers by default.

Prefer:

```text
followers_count
is_following
```

unless public follower identity becomes a deliberate social feature.

### 44.2 Sensitive fields

Do not serialize:

- provider secrets;
- private keys;
- encrypted key material;
- sensitive internal metadata;
- moderation notes;
- private storage internals unnecessarily.

### 44.3 Staff endpoints

Dashboard/admin APIs require explicit staff permissions.

Important administrative commercial mutations should be auditable.

---

## 45. SETTINGS/PREFERENCES MODEL

Split the current all-purpose media settings.

### PlaybackPreferences

Potential fields:

```text
default_speed
skip_forward_seconds
skip_back_seconds
trim_silence
autoplay
streaming_quality
```

### DownloadPreferences

```text
download_over_cellular
auto_download_followed
download_quality
```

### NotificationPreferences

```text
new_episode
team_updates
premium_release
```

### Client-local state

Keep client-side unless cross-device sync is explicitly needed:

```text
current volume
active sleep timer
temporary EQ state
current cast device
cache eviction implementation
```

### Server processing policy

Transcription provider, model, automatic processing, and limits belong to server/content-processing configuration.

---

## 46. CAPABILITIES TO PRESERVE

Preserve the product value represented by:

```text
Podcast
Episode
Season
audio assets
signed streaming
progressive streaming
HLS
previews
chapters
transcription
summaries
playback progress
queue
playlists
reactions
comments
paid memberships
entitlements
sports taxonomy
recommendations
analytics
editorial rails
Celery
Redis
object storage/CDN
DRF/OpenAPI
```

A current class may disappear while its valid product capability remains.

---

## 47. IMPLEMENTATIONS TO REMOVE OR DEPRECATE

Subject to caller/data verification:

### Remove

- legacy TensorFlow/TensorFlow-Datasets recommender;
- duplicate recommendation implementations;
- Oscar-derived dynamic class-loading layer;
- Oscar-style URL/AppConfig machinery where unnecessary;
- local raw bank-card/CVV processing;
- duplicate subscription state;
- duplicate queue order/position;
- category-to-plan gating;
- speculative AddOn commerce;
- stale/commented entitlement purchase pathways;
- legacy forum after migration verification;
- unused promotion variants;
- dead code/imports/comments.

### Deprecate / feature-flag

- current custom offline DRM/licensing pipeline.

### Refactor

- promotions -> editorial rails;
- playback history -> canonical PlaybackProgress;
- subscriber/follow terminology -> Follow;
- ML -> offline worker/training workflow;
- media settings -> preference/config domains.

---

## 48. FEATURES NOT TO ADD DURING CORE REFACTOR

The agent must not expand scope with:

- new plan tiers;
- extra payment providers;
- Kafka;
- Kubernetes-specific redesign;
- microservice decomposition;
- blockchain/token features;
- full social-network graph;
- direct messaging;
- arbitrary marketplace/e-commerce;
- creator marketplace;
- new custom DRM;
- unrelated AI chat;
- live rooms;
- large video expansion;
- complex ad-tech.

The current task is convergence.

---

## 49. POST-REFACTOR PRODUCT ROADMAP

Do not build these before core gates pass.

### Phase A

- team/player/competition follows;
- sports-aware personalized home;
- transcript search;
- timestamp sharing;
- bookmarks.

### Phase B

- timestamp comments;
- polls;
- creator replies;
- enhanced moderation.

### Phase C

- smart playlists;
- per-show playback preferences;
- skip silence/voice enhancement;
- richer notifications.

### Phase D

- video podcasts;
- private premium RSS;
- mature native offline DRM;
- live matchday audio/community;
- advanced ML recommendation.

---

## 50. PHASED IMPLEMENTATION PLAN

The implementation must proceed in phases.

Do not perform an uncontrolled repository-wide rewrite.

### PHASE 0 — BASELINE, INVENTORY, SAFETY

Objectives:

1. reproducible baseline;
2. configuration correction;
3. CI;
4. dependency inventory;
5. route/model/task/signal inventory;
6. documentation scaffolding;
7. `SANFOOTBALL_IMPLEMENTATION_STATUS.md`.

Required outputs:

```text
README.md
.env.example
docs/architecture-current.md
docs/refactor-plan.md
SANFOOTBALL_IMPLEMENTATION_STATUS.md
CI workflow
explicit settings modules
dependency inventory
```

No destructive domain migration yet.

Acceptance:

- app starts in development;
- app can start with production settings using appropriately configured dependencies;
- tests execute;
- `django check` passes;
- OpenAPI/schema generation works.

### PHASE 1 — CHARACTERIZATION TESTS

Before invasive replacement, capture desired current behavior.

Add:

- access tests;
- stream tests;
- queue tests;
- playback tests;
- billing state tests where meaningful;
- migration fixtures.

Known defects must be documented as intentional changes, not frozen as “correct” behavior.

### PHASE 2 — CONFIGURATION/DEPENDENCY INFRASTRUCTURE

Do:

- explicit settings;
- secret handling;
- dependency grouping;
- duplicate-dependency removal;
- ML/media isolation;
- logging;
- request IDs;
- health endpoints.

Acceptance:

- web startup has no heavyweight recommendation training/import side effects.

### PHASE 3 — LEGACY FRAMEWORK REMOVAL

Do:

- normal Django URL includes;
- remove Oscar dynamic loading;
- migrate callers;
- simplify API app registration.

Acceptance:

- normal Django startup/URLs work without legacy framework machinery.

### PHASE 4 — CONTENT CONSOLIDATION

Do:

- Podcast/Season/Episode canonical models;
- explicit release/visibility;
- category decoupling;
- content/media relationship cleanup;
- data migration.

Acceptance:

- public IDs/URLs preserved or compatibility exists.

### PHASE 5 — MEMBERSHIP/ACCESS

Do:

- stable plan code;
- Price;
- canonical Subscription;
- evaluate/remove Membership wrapper;
- canonical Entitlement;
- AccessPolicy;
- access matrix tests;
- stream integration.

Acceptance:

- no protected-media path bypasses AccessPolicy.

### PHASE 6 — BILLING

Do:

- provider boundary;
- idempotent webhook;
- card-handling removal;
- subscription reconciliation;
- refund/cancel behavior.

Acceptance:

- duplicate/out-of-order provider-event tests pass.

### PHASE 7 — PLAYBACK/QUEUE

Do:

- PlaybackProgress;
- PlaybackQueue;
- QueueItem;
- merge;
- command-style queue API;
- concurrency tests.

Acceptance:

- one queue ordering field;
- no manager/filter references nonexistent model fields.

### PHASE 8 — LIBRARY

Do:

- PodcastFollow migration;
- playlist normalization;
- remove follow/subscription terminology collision;
- bookmark foundation if appropriate.

Acceptance:

- free follow and paid subscription are distinct at model/service/API level.

### PHASE 9 — MEDIA DELIVERY

Do:

- AudioVariant;
- role/format separation;
- authorization;
- processing jobs;
- CDN signing cleanup;
- preview policy.

Acceptance:

- full protected media cannot be retrieved without authorization.

### PHASE 10 — TRANSCRIPTION/CHAPTER/AI

Do:

- canonical transcript;
- processing policy;
- chapter cleanup;
- summary provenance;
- worker isolation.

Acceptance:

- server processing provider is not a listener preference.

### PHASE 11 — COMMUNITY

Do:

- canonical comments;
- migrate/remove forum;
- reaction constraints;
- moderation baseline.

### PHASE 12 — DISCOVERY/EDITORIAL

Do:

- remove old recommender;
- decouple from serializers;
- heuristic sports-aware recommendation;
- HomeRail;
- caching.

Acceptance:

- no model training at import;
- home feed uses lightweight bounded serializers.

### PHASE 13 — OFFLINE

Do:

- deprecate unsafe/custom paths;
- signed-download replacement as needed;
- preserve/archive legacy package/license data;
- document future DRM.

### PHASE 14 — HARDENING

Do:

- query profiling;
- load tests;
- security review;
- rate limits;
- dependency audit;
- backup/restore verification;
- deployment runbooks;
- deprecation cleanup.


---

## 51. PHASE GATES

A phase is not complete because files were moved.

Every phase must satisfy:

1. relevant tests pass;
2. migrations are reviewed and reproducible;
3. documentation is updated;
4. old callers are removed or compatibility is explicitly documented;
5. no new high-severity lint/type/security errors are introduced;
6. no known authorization regression remains;
7. no unjustified N+1/query regression remains;
8. `SANFOOTBALL_IMPLEMENTATION_STATUS.md` is updated;
9. superseded implementation is actually deleted when migration is complete.

The agent must not move to the next phase while leaving critical prior-phase TODOs hidden inside production code.

---

## 52. `SANFOOTBALL_IMPLEMENTATION_STATUS.md`

Maintain a living status file.

Suggested format:

```markdown
# SANFootball Implementation Status

## Current Phase
Phase 5 — Membership and Access

## Completed
- ...

## In Progress
- ...

## Deferred
- ...

## Legacy Components Remaining
- ...

## Data Migrations
- ...

## Compatibility Routes
- ...

## Known Risks
- ...

## Next Actions
- ...
```

This document is required specifically to prevent another half-complete generation of architecture from accumulating.

---

## 53. AGENT EXECUTION PROTOCOL

### 53.1 Before changing any domain

Inspect:

- models;
- migrations;
- imports/callers;
- API routes;
- serializers;
- admin;
- signals;
- tasks;
- settings;
- tests;
- frontend assumptions where discoverable.

### 53.2 Trace callers before deletion

Do not delete a class only because it appears obsolete.

Search its actual callers.

If no caller exists and no data/migration dependency requires it, remove it.

### 53.3 Characterize high-risk behavior

For access, billing, queue, playback, and media authorization:

1. identify intended behavior;
2. create tests;
3. then replace implementation.

### 53.4 Implement incrementally

Prefer coherent, reviewable steps.

Do not create a giant branch where:

- models;
- APIs;
- settings;
- migrations;
- auth;
- billing;
- media;
- recommendations

all change without intermediate validation.

### 53.5 Do not preserve defects

If old behavior is clearly incorrect and conflicts with this specification, fix it and document the intentional behavior change.

### 53.6 Do not introduce silent fallback

Broad exception swallowing is forbidden in critical paths.

Use expected exceptions and explicit error handling.

### 53.7 Keep the repository runnable

At every major phase boundary:

- Django boots;
- relevant tests pass;
- migrations are valid;
- CI remains usable.

---

## 54. DEFINITION OF DONE FOR THE ENTIRE REFACTOR

The refactor is complete only when all of the following are true.

### 54.1 Architecture

- domain boundaries are clear;
- API folders are no longer a forest of pseudo-domain Django apps;
- obsolete Oscar-style dynamic loading is gone or any justified remnant is minimal and documented;
- duplicate recommendation systems are gone;
- forum/community duplication is resolved;
- one queue architecture remains;
- one playback-progress architecture remains;
- one paid-subscription architecture remains;
- free following is distinct from paid subscription;
- one AccessPolicy controls protected resource actions.

### 54.2 Data

- legacy data has been migrated or intentionally archived;
- integrity checks pass;
- public content identifiers remain stable or compatibility exists;
- destructive cleanup follows verification.

### 54.3 Commercial

- raw card handling is removed unless formally justified;
- provider webhooks are verified and idempotent;
- subscription state is canonical;
- entitlement history is auditable;
- access decisions derive from canonical state.

### 54.4 Security

- production settings are deterministic;
- protected media cannot bypass authorization;
- secrets are environment-managed;
- sensitive endpoints are rate-limited;
- uploads are validated;
- SSRF-sensitive operations are hardened;
- dependency audit is clean or exceptions are documented.

### 54.5 Performance

- major endpoints have bounded query counts;
- home feed does not serialize unbounded nested structures;
- expensive media/ML work is outside request processing;
- cache is optional for correctness;
- no import-time model training remains.

### 54.6 Testing

- access matrix passes;
- queue merge/concurrency tests pass;
- billing replay tests pass;
- stream authorization tests pass;
- migration tests cover replaced critical data.

### 54.7 Documentation

- README is useful;
- architecture docs exist;
- access/billing/media/playback docs exist;
- ADRs record material decisions;
- OpenAPI is generated;
- operations/deployment runbooks exist.

### 54.8 Maintainability

- no large blocks of commented legacy code;
- no duplicate state fields for the same concept;
- no domain service imports API serializers;
- no critical transition depends only on hidden signals;
- no third-generation duplicate implementation has been introduced.

---

## 55. REQUIRED END-TO-END ACCEPTANCE SCENARIOS

These scenarios should eventually be executable.

### 55.1 Anonymous public listener

1. Open public podcast.
2. View public episode.
3. Play full public audio.
4. Add episode to anonymous queue.
5. No premium media credential is exposed.

### 55.2 Anonymous premium preview

1. Open premium episode metadata.
2. AccessPolicy denies full stream.
3. Preview policy allows preview.
4. Short-lived preview URL is issued.
5. Full URL is never returned.

### 55.3 Login queue merge

1. Anonymous queue contains A, B.
2. Authenticated queue contains B, C.
3. User logs in.
4. Deterministic result preserves existing authenticated order and adds non-duplicate anonymous items.
5. B appears only once.
6. Anonymous queue is retired atomically.

### 55.4 Successful paid subscription

1. User enters provider checkout.
2. Provider reports success.
3. Verified webhook is processed.
4. Canonical Subscription becomes active.
5. AccessPolicy grants qualifying premium episode.
6. Stream service issues full protected media credential.

### 55.5 Duplicate billing webhook

1. Same provider event arrives twice.
2. First processes.
3. Second is recognized by idempotency record.
4. No duplicate subscription/entitlement is created.

### 55.6 Cancel at period end

1. Active user cancels.
2. `cancel_at_period_end=True`.
3. Access continues through current period.
4. Access ends after period expiry.
5. No separate Boolean contradicts status.

### 55.7 Follow versus paid subscription

1. Free user follows a podcast.
2. It appears in Library/New From Followed Shows.
3. User has not become a paying subscriber.
4. Premium content remains gated.
5. API terminology clearly distinguishes the concepts.

### 55.8 Continue Listening

1. User plays 20 minutes of a 60-minute episode.
2. Progress is checkpointed.
3. Home feed shows Continue Listening.
4. Resume starts near stored position.
5. Completion removes item from Continue Listening.

### 55.9 Protected download

1. Plan grants download capability.
2. AccessPolicy evaluates `DOWNLOAD`.
3. Signed TTL-bound URL is issued.
4. Non-entitled user receives structured denial.
5. `STREAM` permission alone does not automatically imply `DOWNLOAD`.

### 55.10 Transcript search — future target

1. User searches a player/topic.
2. Transcript search finds a spoken occurrence.
3. Result contains snippet and timestamp.
4. Player opens episode at timestamp.

---

## 56. FOOTBALL-SPECIFIC PRODUCT ENHANCEMENTS AFTER STABILIZATION

### 56.1 Match-linked listening

A match page should eventually be able to surface:

```text
preview episodes
pre-match show
post-match reaction
tactical breakdown
player-focused analysis
```

### 56.2 Entity pages

Team/player pages may show:

```text
latest episodes
recent mentions
timestamped moments
follow action
related discussions
```

### 56.3 Matchday mode

Home feed may prioritize:

```text
Today’s Matches
Previews
Post-Match Episodes
Team Feeds
```

### 56.4 Transcript-driven clips

Once transcript/media architecture is stable, editors may create clips/social assets from timestamp ranges.

This is a later workflow, not a Phase 0–14 prerequisite.

---

## 57. INDUSTRY / INTERNATIONAL BEST-PRACTICE ALIGNMENT

Where relevant, align with:

- Django deployment/security guidance;
- Django ORM transaction best practices;
- OWASP Top 10;
- OWASP API Security Top 10;
- Twelve-Factor principles where appropriate;
- PCI scope minimization;
- principle of least privilege;
- OpenAPI;
- secure private-media delivery;
- idempotent webhook handling;
- structured observability;
- database-backed integrity;
- safe distributed retry semantics.

Do not cite “best practice” as an excuse to add unnecessary infrastructure.

Every pattern must fit SANFootball’s real product.

---

## 58. CLOUD / STORAGE PERMISSIONS

Whether using AWS or compatible providers:

### Web process

Grant only the storage/signing permissions required by normal application behavior.

### Media worker

Grant only the processing/storage permissions required for its jobs.

### Key management

If KMS/encryption remains or returns later:

- least privilege;
- audit key operations;
- never log key material;
- isolate environments;
- rotate credentials intentionally.

### Environment separation

Development, staging, and production must not casually share:

- production database;
- production buckets;
- signing keys;
- payment credentials;
- webhook secrets.

---

## 59. DATA RETENTION AND PRIVACY

Create documented retention behavior for:

- analytics events;
- raw IP addresses;
- listening history;
- deleted accounts;
- payment metadata;
- comments;
- device records;
- offline license records if retained;
- transcription/media artifacts.

The architecture should permit user-data deletion/export where legally or product-required.

Do not retain sensitive data indefinitely because no cleanup job was designed.

---

## 60. ADMIN AND EDITORIAL OPERATIONS

The administrative surface should support real SANFootball workflows.

Editors should be able to manage:

- podcasts;
- seasons;
- episodes;
- publication/release timing;
- premium/public visibility;
- artwork;
- chapters;
- transcripts;
- sports relationships;
- editorial rails;
- campaign banners.

Commercial operators should be able to inspect:

- subscription state;
- provider references;
- webhook processing status;
- entitlement grants/revocations;
- payment/invoice references where required.

Never expose provider secrets or raw key material.

Important administrative commercial changes should be auditable.

---

## 61. RSS / IMPORT / EXPORT

If SANFootball hosts and distributes podcasts:

### 61.1 Public RSS

Generate standards-compliant public feeds.

### 61.2 Private premium RSS

May be added after the commercial architecture is stable.

Use revocable opaque tokens.

Do not put raw user IDs/secrets directly in feed URLs.

### 61.3 Remote RSS import

If remote feeds are imported:

- validate URLs;
- prevent SSRF;
- limit response size/time;
- parse defensively;
- track source/feed errors.

---

## 62. COMPATIBILITY POLICY

Classify every breaking change as:

```text
INTERNAL
DATA
API
URL
CLIENT
OPERATIONS
```

### Internal

May change after callers migrate.

### Data

Requires safe migration.

### API/client

Requires version/deprecation if active clients rely on it.

### URL

Preserve public podcast/episode URLs where practical.

### Deprecation record

For active old routes, document:

```text
old route
replacement
deprecation date
planned removal
usage metric where available
```

Compatibility is a managed transition, not permanent duplication.

---

## 63. KEEP THE SYSTEM A MODULAR MONOLITH

Do not transform this refactor into a microservices project.

Preferred deployment processes may include:

```text
Django web
Celery default worker
media worker
transcription/ML worker
```

Separate process responsibilities do not require separate networked microservices.

A modular Django monolith is preferable to distributed architectural confusion.

---

## 64. WHEN A COMPONENT DESERVES ITS OWN DJANGO APP

Create a Django app when it has:

- clear domain ownership;
- models/migrations or a strong independent domain;
- meaningful business vocabulary;
- independent test surface.

Do not create a Django app merely because it contains:

- serializers;
- URLs;
- two helper files;
- a dashboard presentation layer.

---

## 65. DELETION DISCIPLINE

Deletion is part of the project, not optional cleanup.

Once replacement is verified:

1. remove old imports;
2. remove old routes;
3. remove old services;
4. remove old models after migration/contract;
5. remove unused dependencies;
6. remove obsolete docs;
7. update diagrams;
8. remove compatibility code when its window ends.

A refactor that only adds new architecture beside old architecture is considered unsuccessful.

---

## 66. CODE-REVIEW CHECKLIST

For every substantial change, answer the following.

### Domain

- Does this code belong here?
- Is there already another implementation of the same concept?
- Is terminology consistent with this specification?

### Data

- Are constraints correct?
- Are indexes justified?
- Is data migration safe?
- Is rollback/reconciliation possible?

### Security

- Is authorization server-side?
- Can the operation be replayed?
- Does it expose protected information?
- Are external inputs trusted too much?

### Transactions

- Does this need atomicity?
- Can concurrent requests corrupt state?
- Should `select_for_update()` be used?

### Performance

- Query count?
- N+1?
- large in-memory collections?
- expensive work in request path?
- avoidable external calls?

### API

- Is response bounded?
- Is pagination required?
- Is error structured?
- Is versioning/deprecation required?

### Tests

- happy path?
- denial/error?
- duplicate/retry?
- concurrency?
- migration?

### Operations

- is it observable?
- are failures actionable?
- can it be safely retried?

### Cleanup

- what old code can now be deleted?

---

## 67. REQUIRED REPOSITORY DOCUMENTS

At the end of the refactor, the repository should include at minimum:

```text
AGENTS.md
README.md
.env.example
SANFOOTBALL_IMPLEMENTATION_STATUS.md
CHANGELOG.md or equivalent release notes strategy

docs/
    architecture.md
    domains.md
    access-control.md
    billing.md
    media.md
    playback.md
    queue.md
    recommendations.md
    security.md
    testing.md
    deployment.md
    operations.md
    migrations.md
    adr/
```

Where practical, include:

- Mermaid architecture diagrams;
- state diagrams for subscription;
- access decision flow;
- media-processing flow;
- queue merge flow;
- deployment topology.

Documentation should be maintained with implementation, not generated once and abandoned.

---

## 68. REQUIRED FIRST ACTIONS FOR THE IMPLEMENTATION AGENT

When an implementation agent receives the repository and this `AGENTS.md`, the **first development cycle** must be:

1. read this entire file;
2. inspect the full repository tree;
3. inspect all Django app registrations;
4. inspect all migrations;
5. map every model and relation;
6. map all public and dashboard API routes;
7. map all Django signals;
8. map all Celery tasks;
9. trace callers of:
   - `core.application`;
   - `core.loading`;
   - membership/access services;
   - queue models/services;
   - legacy recommender;
   - current recommendation domain;
   - offline media;
   - billing/card code;
   - forum/comments;
   - promotions/editorial code;
10. identify committed configuration/secrets risks;
11. create `docs/architecture-current.md`;
12. create `docs/refactor-plan.md`;
13. create `SANFOOTBALL_IMPLEMENTATION_STATUS.md`;
14. establish or repair CI;
15. establish explicit settings modules;
16. run the current tests;
17. record pre-existing failures separately from refactor-induced failures;
18. create high-risk characterization tests;
19. then begin Phase 2 and continue sequentially.

The agent must **not** begin by randomly moving folders.

The first deliverable is:

> **understanding + safety infrastructure**

The second is:

> **canonical domain migration**

The third is:

> **deletion of the superseded implementation**

Repeat that sequence until the architecture converges.

---

## 69. FINAL AGENT DIRECTIVE

The objective is not to make SANFootball architecturally fashionable.

The objective is to produce a codebase that is:

- understandable;
- cohesive;
- secure;
- fast;
- scalable;
- testable;
- observable;
- migration-safe;
- production-grade;
- efficient to operate;
- straightforward to extend.

The central rule of this specification is:

> **Every time a new canonical implementation replaces a legacy concept, finish the migration and delete the legacy implementation. Do not allow SANFootball to accumulate another parallel generation of the same feature.**

When choosing between preserving a complicated historical abstraction and implementing the simpler canonical model specified here, prefer the simpler canonical domain model **provided user data, security, and active public/client contracts are migrated safely**.

The target platform should ultimately be understandable through a relatively small set of strong concepts:

```text
Podcast
Season
Episode
AudioVariant
Transcript
Chapter

PlaybackProgress
PlaybackQueue
QueueItem
Playlist
Bookmark

PodcastFollow
TeamFollow
PlayerFollow
CompetitionFollow

Plan
Price
Subscription
Entitlement
AccessPolicy

Comment
Reaction
Poll

Recommendation
HomeRail
AnalyticsEvent

Team
Player
Competition
Match
```

Every additional abstraction must justify itself by clearly supporting these concepts.

---

## END OF GOVERNING SPECIFICATION

---

# PART II — POST-REFACTOR FEATURE EXPANSION, SMART CAPABILITIES, AND PRODUCTION INFRASTRUCTURE

> This part contains the complete later feature-expansion programme plus the production-hosting/infrastructure amendment. It is governed by the master rules above and must extend, never bypass, the canonical architecture established in Part I.

## AGENTS.md

> **Repository authority for the post-refactor evolution of the SanFootball sports podcast platform**
>
> This file is an implementation specification, architectural contract, migration guide, quality gate, and execution plan for coding agents working on this repository.
>
> **Status:** Authoritative for all feature work described in this document.
>
> **Infrastructure amendment:** Updated 2026-08-19 to make production hosting, object storage, direct media upload, CDN/media delivery, managed video, container scaling, database/cache hosting, queue scaling, IaC/CI/CD, disaster recovery, observability, and FinOps explicit architectural requirements.
>
> **Integrated baseline rule:** Part II assumes the canonical architecture defined in Part I of this same file. If a required Part I invariant is not yet true in the repository, the implementation agent MUST complete the necessary Part I canonicalisation before implementing a dependent Part II feature. This file does **not** authorise duplicate models, duplicate services, duplicate state, parallel entitlement systems, competing queue implementations, overlapping recommendation engines, or feature-specific architectural islands.

---

## 0. EXECUTIVE MANDATE

The next stage of SanFootball is not to become a generic collection of podcast features.

The platform must evolve from a modernised podcast application into a **football-first audio and media platform** in which:

- podcasts are first-class content;
- episodes can contain multiple media variants;
- listening is continuous across devices;
- the player is competitive with premium podcast applications;
- transcripts are searchable, accessible, shareable, and semantically useful;
- clubs, players, competitions, fixtures, topics, creators, episodes, chapters, clips, and listener activity are interconnected;
- live football audio can become durable on-demand podcast content;
- membership and entitlement controls remain canonical and reusable;
- discovery becomes football-aware rather than merely episode-aware;
- creator analytics become actionable rather than superficial;
- community activity is tied to content moments and football events;
- offline, mobile-data, casting, and connected-device use cases are treated as core product concerns;
- feature growth must occur without recreating the architectural fragmentation that the refactor was intended to remove;
- media storage and media delivery must scale independently from Django application compute;
- large creator uploads must support direct-to-storage/provider transfer;
- production hosting, deployment, observability, disaster recovery, and cost control are first-class architecture concerns.

The implementation agent MUST build these capabilities incrementally, preserve canonical domain ownership, maintain backward compatibility where required, provide safe data migrations, and delete superseded implementations once callers have migrated.

This document intentionally goes beyond a feature wish list. It defines:

1. the product direction;
2. the architectural boundaries;
3. the canonical domain concepts;
4. the expected data ownership;
5. implementation constraints;
6. integration and event contracts;
7. background-processing requirements;
8. performance requirements;
9. security and privacy requirements;
10. testing requirements;
11. observability requirements;
12. migration and compatibility expectations;
13. phased implementation order;
14. acceptance criteria;
15. explicit anti-patterns;
16. documentation requirements;
17. a first-action protocol for any coding agent.

If an existing repository decision conflicts with this specification, the agent MUST:

1. determine whether the conflict is a legacy implementation that should be migrated;
2. preserve user data;
3. document the conflict;
4. create an ADR when the resolution materially changes architecture;
5. prefer the canonical architecture defined here unless doing so would violate a newer, explicit repository-level instruction.

---

## 1. PRODUCT NORTH STAR

SanFootball should not attempt to win by becoming a smaller Spotify, Apple Podcasts, YouTube Music, Pocket Casts, or TuneIn clone.

Its strategic advantage should be its **football-specific content graph and listening experience**.

The target product model is:

```text
Football Event
      ↕
Club ↔ Player ↔ Manager ↔ Competition ↔ Topic
      ↕
Show ↔ Episode ↔ Chapter ↔ Moment ↔ Clip
      ↕
Creator ↔ Network ↔ Community ↔ Listener
      ↕
Subscription ↔ Membership ↔ Entitlement
```

The intended product evolution is:

```text
Modern podcast platform
        ↓
Premium podcast player
        ↓
Smart personal library
        ↓
Football-aware discovery
        ↓
Creator and listener intelligence
        ↓
Audio/video podcast platform
        ↓
Live + on-demand football audio
        ↓
Match-aware football media ecosystem
```

The implementation MUST preserve this direction.

A new feature is preferred when it strengthens at least one of the following loops:

```text
Discover → Start → Listen → Finish → Follow → Return
```

```text
Match → Discussion → Podcast → Transcript → Clip → Community → Discovery
```

```text
Creator publishes → Audience listens → Analytics reveal behaviour
→ Creator improves content → Audience retention improves
```

```text
Free listener → Engagement → Premium preview → Entitlement conversion
→ Retention → Renewal
```

Features that do not strengthen the core product, introduce excessive architectural complexity, or duplicate existing capabilities should be rejected or deferred.

---

## 2. GOVERNING ASSUMPTIONS

### 2.1 The refactored repository is the baseline

All work in this file assumes that SanFootball has canonical implementations for the following conceptual areas:

- content;
- shows;
- seasons;
- episodes;
- chapters;
- transcripts;
- summaries;
- media;
- listening progress;
- history;
- queue;
- playlists;
- bookmarks;
- downloads;
- search;
- discovery;
- recommendations;
- trending/editorial feeds;
- football entities and feeds;
- comments;
- reactions;
- polls;
- subscriptions;
- memberships;
- entitlements;
- access policy;
- content gating;
- private feeds;
- notifications or a canonical path for adding them;
- background processing;
- settings/configuration.

The agent MUST inspect the repository before assuming exact Python package names, database table names, service class names, URLs, event names, task names, or serializers.

The conceptual boundaries in this document are authoritative even if the repository uses different package names.

### 2.2 Do not redo the refactor during feature work

The agent MUST NOT opportunistically create:

- a second queue;
- a second playlist implementation;
- a second download model;
- a second progress model;
- a second subscription system;
- a separate video-episode domain disconnected from normal episodes;
- a separate premium-content model when entitlements already exist;
- a second recommendation service;
- another comment system specifically for clips or live rooms if the canonical community domain can represent them;
- an independent football entity store for transcript extraction;
- feature-specific settings that bypass canonical configuration;
- a parallel notification framework;
- a parallel analytics event pipeline;
- a separate AI content store when existing transcript/content metadata can be extended.

Where the canonical implementation lacks a capability, extend it.

Where legacy code remains, migrate callers and remove the legacy implementation.

### 2.3 Preserve the modular-monolith discipline unless an ADR proves otherwise

Feature growth alone is NOT justification for splitting the product into microservices.

The default architecture is a modular monolith with:

- strongly defined domain boundaries;
- explicit service interfaces;
- internal events;
- asynchronous jobs for heavy work;
- infrastructure adapters;
- clear transaction boundaries;
- externalisation only when operational evidence warrants it.

Heavy media processing, machine-learning inference, search infrastructure, analytics aggregation, or live-media infrastructure MAY run as separate deployable workers/services when justified, but the application domain MUST still expose clear contracts and retain canonical ownership.

---

## 3. NON-NEGOTIABLE ARCHITECTURAL RULES

### 3.1 One canonical owner per piece of mutable state

Every mutable state concept MUST have one authoritative owner.

Examples:

| Concept | Canonical owner |
|---|---|
| episode metadata | content domain |
| audio/video resources | media/content domain |
| queue ordering | playback/listening domain |
| episode progress | playback/listening domain |
| playlist membership | playback/library domain |
| download intent/status | playback/download domain |
| subscription state | commercial/membership domain |
| entitlement decision | access policy/commercial domain |
| club/player/competition identity | football domain |
| transcript | content/transcript domain |
| transcript entity mention | football/content integration contract |
| comments/reactions/polls | community domain |
| notification preference | notifications domain |
| analytics raw event | analytics domain |
| active playback session | playback domain |
| clip definition | content/media derivative domain |
| live broadcast lifecycle | live/community/media boundary as explicitly designed |
| creator team role | creator/network ownership domain |

No other module may silently maintain a divergent copy.

### 3.2 Server-side authorisation is mandatory

A client-visible flag such as:

```json
{"is_premium": true}
```

is NEVER sufficient authorisation.

Every protected media request, premium transcript, private feed, live room, creator action, analytics view, team-management action, clip export, download token, or ad-free media request MUST be authorised server-side.

The canonical access policy MUST determine:

- whether the user can access the content;
- which media variant is available;
- whether preview restrictions apply;
- whether download is permitted;
- whether clip creation is permitted;
- whether transcript access is permitted;
- whether live participation is permitted;
- whether creator/admin actions are permitted.

### 3.3 All heavy operations must be asynchronous

Normal web/API request paths MUST NOT synchronously perform expensive work such as:

- video transcoding;
- audio transcoding;
- waveform generation;
- transcript generation;
- translation;
- embedding generation;
- semantic indexing;
- entity extraction;
- automatic chapter generation;
- silence/intro detection;
- clip rendering;
- quote-card rendering;
- large analytics aggregation;
- recommendation recomputation;
- annual recap generation;
- OPML bulk import processing;
- large RSS backfills;
- notification fan-out;
- live-recording finalisation.

The request path should create or update canonical state, enqueue work, and return an appropriate status representation.

### 3.4 Idempotency is mandatory for retryable work

Every background workflow that may be retried MUST be idempotent.

Examples:

- RSS episode import;
- media processing;
- transcript creation;
- entity extraction;
- clip rendering;
- notification delivery;
- subscription webhook processing;
- analytics compaction;
- smart-download evaluation;
- live-to-episode conversion;
- annual recap generation.

Use deterministic idempotency keys where possible.

### 3.5 Avoid signal-driven hidden business logic

Framework signals MAY publish lightweight events or maintain unavoidable framework integrations.

They MUST NOT become the primary place where complex business workflows are orchestrated.

Prefer explicit application services and domain events.

### 3.6 No unbounded queries

Every list API, feed, history endpoint, transcript search, analytics query, comments endpoint, notification list, clip list, or creator listing MUST be bounded and paginated where appropriate.

Avoid accidental full-table materialisation.

### 3.7 No N+1 query behaviour

Every major API path MUST be profiled or tested for query count where practical.

Use:

- select-related loading;
- prefetching;
- batched loaders;
- denormalised read projections where justified;
- caching where appropriate.

Do not hide query explosion behind serializers.

### 3.8 Compatibility must be intentional

When changing an existing API:

- prefer additive changes;
- version breaking changes;
- deprecate before removing where external clients may depend on it;
- document migration paths;
- migrate internal callers before deletion;
- maintain tests for supported compatibility windows.

---

## 4. CANONICAL DOMAIN MAP

The exact repository directory names may differ. The following is the conceptual ownership model.

```text
content/
    shows
    seasons
    episodes
    chapters
    transcripts
    summaries
    media
    clips
    derivatives

playback/
    player_preferences
    sessions
    progress
    history
    queue
    playlists
    bookmarks
    downloads
    library
    smart_rules

discovery/
    search
    transcript_search
    semantic_search
    recommendations
    trending
    editorial
    home_feed

football/
    clubs
    players
    managers
    competitions
    fixtures
    topics
    entity_mentions
    event_content_links

community/
    comments
    reactions
    polls
    moderation
    live_interaction

commercial/
    products
    plans
    subscriptions
    memberships
    entitlements
    access_policy
    premium_variants
    conversion

creators/
    creator_profiles
    networks
    channels
    teams
    roles
    publishing

analytics/
    events
    listening
    creator_metrics
    funnels
    retention
    reporting
    recaps

notifications/
    preferences
    subscriptions
    fanout
    delivery

live/
    broadcasts
    rooms
    participants
    recordings
    conversion_to_episode

integrations/
    rss
    opml
    casting
    automotive
    external_devices
```

These are ownership boundaries, not a requirement to create one application/package for each bullet.

The agent MUST map these concepts to the refactored repository and reuse existing packages where appropriate.

---

## 5. FEATURE PROGRAMME OVERVIEW

The product programme is divided into the following major increments:

1. advanced playback;
2. smart library and queue automation;
3. smart downloads;
4. cross-device playback;
5. RSS and OPML portability;
6. clips and quote sharing;
7. video podcasts;
8. semantic transcript search;
9. football entity extraction and knowledge links;
10. entity-based following;
11. intelligent notifications;
12. highlights discovery;
13. creator analytics;
14. subscription conversion analytics;
15. ad-free/premium media variants;
16. podcast networks/channels;
17. creator teams and permissions;
18. live podcasting;
19. matchday rooms;
20. match-aware chapters;
21. match listening collections;
22. personalised football home;
23. listener profiles and annual recaps;
24. tasteful achievements;
25. connected-device playback;
26. low-bandwidth/data-saver mode;
27. transcript accessibility and translation;
28. creator-side AI assistance.

The features MUST be implemented in phases later in this document rather than all at once.

---

## 6. ADVANCED PLAYER

### 6.1 Objective

Make SanFootball's player competitive with dedicated premium podcast players.

The player is not merely a UI component. It is a coordinated system consisting of:

- client playback engine;
- server-backed preferences;
- canonical progress;
- queue;
- playback session;
- media selection;
- entitlement enforcement;
- device state;
- optional audio-processing effects.

### 6.2 Required playback controls

Support:

- play;
- pause;
- seek;
- previous;
- next;
- configurable rewind;
- configurable forward skip;
- playback speed;
- chapter navigation;
- queue navigation;
- sleep timer;
- stop-after-current-episode;
- resume from canonical progress;
- explicit restart;
- mark played/unplayed;
- bookmark current timestamp.

### 6.3 Playback speed

Support an implementation-defined safe range, with a suggested product range of approximately:

```text
0.5x – 3.0x
```

The exact UI increments may be product-configurable.

Persist:

- global default playback rate;
- per-show override;
- optional per-device temporary override.

Resolution order:

```text
explicit session override
    ↓
per-show preference
    ↓
global user preference
    ↓
platform default
```

Do not store playback rate independently in multiple profile/settings models.

### 6.4 Silence trimming

Silence trimming should initially be implemented client-side where supported.

Requirements:

- user-controlled;
- off by default unless product explicitly decides otherwise;
- gracefully disabled on unsupported clients;
- must not corrupt canonical timestamps;
- chapter/transcript/bookmark timestamps remain based on original media time;
- analytics MUST distinguish media-time position from wall-clock listening time.

Do not rewrite stored episode audio merely to support ordinary listener silence trimming.

### 6.5 Voice enhancement and loudness

Where supported, provide:

- loudness normalisation;
- speech/voice enhancement;
- optional gain boost.

Client-side processing is preferred for lightweight effects.

Server-side derivative media SHOULD only be introduced where there is a clear need and storage/processing cost is justified.

### 6.6 Intro/outro skipping

Support both:

- creator-defined intro/outro markers;
- automatically detected recurring segments.

Canonical model should support episode-specific playback markers:

```text
PlaybackMarker
    id
    episode_id
    type
    start_ms
    end_ms
    source
    confidence
    created_at
    updated_at
```

Suggested types:

- INTRO;
- OUTRO;
- AD_BREAK;
- RECAP;
- CUSTOM.

The agent MUST NOT overload normal chapter records if playback markers and editorial chapters have different semantics.

Automatic detection must:

- run asynchronously;
- produce confidence;
- never silently override creator-defined markers;
- allow review or disablement;
- preserve original media timestamps.

Per-user and per-show settings may include:

- auto-skip intro;
- auto-skip outro;
- auto-skip creator-marked ad breaks where product policy permits.

### 6.7 Sleep timer

Support:

- fixed duration;
- end of current chapter;
- end of current episode.

Sleep state is normally client/session state and need not become durable long-term user history.

### 6.8 Acceptance criteria

At minimum:

- progress is preserved regardless of playback rate;
- seeking does not cause duplicate analytics completion events;
- per-show playback settings override global settings;
- protected media remains protected regardless of client controls;
- skip markers are deterministic and testable;
- unsupported playback effects fail gracefully.

---

## 7. SMART LIBRARY, SMART PLAYLISTS, AND EPISODE INBOX

### 7.1 Objective

Move the product from passive subscriptions to an actively managed personal listening system.

### 7.2 Manual and smart playlists

A playlist MUST have an explicit type:

```text
MANUAL
SMART
```

A smart playlist is a saved query/rule set, not a manually materialised copy of every matching episode unless a cached projection is intentionally maintained.

Possible filters include:

- followed shows;
- specific shows;
- clubs;
- players;
- managers;
- competitions;
- topics;
- published date;
- duration;
- played/unplayed;
- completed/in-progress;
- downloaded/not downloaded;
- premium/free;
- media type;
- language;
- season;
- explicit content flag if supported;
- episode type;
- bookmarked state.

Possible sorting includes:

- newest first;
- oldest first;
- shortest first;
- longest first;
- most recently added;
- editorial rank;
- recommendation score;
- manual priority groups.

### 7.3 Rule representation

Rules should use a validated structured representation.

Do NOT evaluate arbitrary user-authored Python, SQL, JavaScript, templates, or expressions.

Example conceptual payload:

```json
{
  "all": [
    {"field": "played", "operator": "eq", "value": false},
    {"field": "published_at", "operator": "within_days", "value": 7}
  ],
  "any": [
    {"field": "club_id", "operator": "in", "value": ["..."]},
    {"field": "topic_id", "operator": "in", "value": ["..."]}
  ],
  "sort": [
    {"field": "published_at", "direction": "desc"}
  ]
}
```

The server MUST validate fields, operators, values, permissions, and query complexity.

### 7.4 Episode Inbox

Followed-content delivery should support an Inbox concept distinct from queue.

Inbox actions:

- play;
- add to queue;
- save;
- download;
- archive;
- dismiss/ignore;
- mark played;
- bulk archive.

The inbox SHOULD represent "new content available for my attention."

The queue SHOULD represent "content I intend to listen to in an ordered sequence."

Do not conflate these states.

### 7.5 Inbox generation

Inbox entries may arise from:

- followed shows;
- followed creators;
- followed clubs;
- followed players;
- followed competitions;
- smart subscription rules.

Generation MUST be idempotent.

Duplicate feed routes must not create duplicate inbox items.

### 7.6 Acceptance criteria

- Smart playlists are deterministic.
- Smart rules cannot create arbitrary expensive queries.
- Inbox and queue remain semantically distinct.
- Bulk actions are transactional or safely retryable.
- Deleted/unavailable episodes are handled gracefully.
- Premium episodes may appear in discovery/inbox where product policy allows, but access policy still governs playback.

---

## 8. SMART DOWNLOADS

### 8.1 Objective

Make offline use automatic, predictable, storage-aware, and suitable for mobile users.

### 8.2 Policy examples

Support configurable rules such as:

- automatically download newest N episodes from a show;
- download new episodes matching a smart playlist;
- download followed-club episodes;
- Wi-Fi only;
- charging only where native client capabilities allow;
- data-saver compatibility;
- maximum device storage allocation;
- delete N hours/days after completion;
- retain bookmarked episodes;
- retain explicitly pinned downloads;
- delete oldest completed episodes first;
- never auto-delete premium content until entitlement rules require it.

### 8.3 Server and client responsibility

The server stores:

- user policy;
- episode eligibility;
- download permission;
- media variant metadata;
- signed/authorised download access;
- optional synchronised download intention.

The device controls:

- actual local file;
- available disk space;
- network state;
- charging state;
- local eviction;
- operating-system background restrictions.

Do not pretend the server can guarantee a file remains physically downloaded on a device.

### 8.4 Download security

Premium downloads MUST use:

- authenticated or signed access;
- expiry;
- entitlement checks;
- non-guessable resource identifiers;
- revocation strategy appropriate to the media delivery architecture.

Avoid permanent public premium media URLs.

### 8.5 Data saver

Smart downloads MUST coordinate with low-bandwidth media selection.

Example:

```text
Wi-Fi:
    preferred_audio_quality = HIGH

Mobile:
    preferred_audio_quality = DATA_SAVER
```

### 8.6 Acceptance criteria

- Download rules do not create duplicate download requests.
- Policy evaluation is idempotent.
- Storage caps are enforced device-side.
- Entitlement checks remain server-side.
- Removing a rule does not silently delete manually pinned content.
- Offline metadata remains usable without network access on supported clients.

---

## 9. CROSS-DEVICE PLAYBACK AND ACTIVE PLAYBACK SESSION

### 9.1 Objective

Allow a listener to move naturally between web, mobile, tablet, television, vehicle, or another supported device.

### 9.2 Canonical playback session

Introduce or extend a canonical `PlaybackSession` concept.

Suggested conceptual fields:

```text
PlaybackSession
    id
    user_id
    episode_id
    media_variant_id
    device_id
    queue_id
    queue_item_id
    position_ms
    duration_ms
    playback_rate
    chapter_id
    state
    started_at
    last_active_at
    version
```

State may include:

- PLAYING;
- PAUSED;
- STOPPED;
- ENDED.

Do not confuse durable listening progress with ephemeral active session state.

### 9.3 Device identity

Represent devices without invasive fingerprinting.

Prefer application-generated device identifiers with user-visible names.

Example:

```text
Chrome on Windows
Android Phone
Living Room TV
Car
```

Allow users to revoke devices where authentication architecture supports it.

### 9.4 Synchronisation

Use optimistic concurrency or a monotonically increasing version/timestamp to prevent stale clients from overwriting newer progress.

Define conflict rules.

Example:

- newest authoritative active session may win;
- a client that has been offline for hours should not automatically rewind server progress unless user explicitly seeks backward;
- explicit seek events should be distinguishable from passive heartbeat updates.

### 9.5 Handoff

Support:

- continue on this device;
- transfer active playback;
- resume from latest canonical position.

Real-time transport MAY use WebSocket/SSE/event infrastructure already present.

Do not require real-time transport for correctness; durable state must remain authoritative.

### 9.6 Privacy

Users MUST be able to understand what device/session information is stored.

Do not expose active device information to other users by default.

### 9.7 Acceptance criteria

- stale session updates cannot easily overwrite newer progress;
- explicit rewind is preserved;
- duplicate heartbeats are harmless;
- session loss does not lose durable progress;
- entitlement changes are rechecked when transferring playback;
- queue handoff preserves ordering.

---

## 10. RSS AND OPML IMPORT/EXPORT

### 10.1 Objective

Reduce switching cost and allow SanFootball to coexist with the wider podcast ecosystem.

### 10.2 External RSS feed subscriptions

Users may add an external podcast feed URL.

Requirements:

- validate URL;
- restrict dangerous schemes;
- defend against SSRF;
- fetch through controlled infrastructure;
- impose response-size limits;
- impose timeouts;
- validate content type where possible;
- parse defensively;
- normalise feed identity;
- prevent duplicate subscription records;
- refresh asynchronously;
- support ETag/Last-Modified;
- rate-limit refreshes;
- respect reasonable remote server behaviour;
- quarantine malformed feeds rather than breaking ingestion.

### 10.3 SSRF requirements

RSS ingestion is a major security boundary.

The fetcher MUST reject or safely control access to:

- localhost;
- loopback;
- link-local addresses;
- private network ranges;
- cloud metadata endpoints;
- unsupported protocols;
- redirect chains that resolve to forbidden networks.

DNS rebinding concerns must be considered.

### 10.4 OPML import

Support standard OPML subscription import.

Large imports MUST:

- run asynchronously;
- expose progress;
- deduplicate feeds;
- report invalid/unreachable feeds;
- permit partial success;
- remain idempotent.

Do not fail an entire import because one feed is invalid.

### 10.5 OPML export

Users should be able to export supported subscriptions in a portable format.

Do not include credentials or secret private-feed tokens in exported OPML without an explicit, secure product decision.

### 10.6 External content boundaries

Externally sourced episodes MUST remain distinguishable from SanFootball-hosted content.

Do not accidentally expose creator-only SanFootball workflows for external feeds.

### 10.7 Acceptance criteria

- duplicate URLs resolve to canonical feed subscriptions;
- SSRF protections are tested;
- OPML import is restartable;
- private credentials are not leaked;
- feed refresh is bounded and observable.

---

## 11. CLIPS AND SHAREABLE AUDIO/VIDEO MOMENTS

### 11.1 Objective

Turn memorable football discussion moments into a user-acquisition and discovery loop.

### 11.2 Canonical Clip

A clip should reference canonical source media rather than becoming an unrelated content type.

Conceptual model:

```text
Clip
    id
    episode_id
    media_variant_id
    creator_user_id
    start_ms
    end_ms
    title
    transcript_excerpt
    visibility
    status
    rendered_asset_id
    created_at
```

Possible visibility:

- PRIVATE;
- UNLISTED;
- PUBLIC.

### 11.3 Duration controls

Set product-configurable limits.

The server MUST validate:

- start < end;
- bounds are inside episode duration;
- clip length is allowed;
- source episode is accessible;
- source content is clip-permitted.

Premium content may have stricter clip rules.

### 11.4 Rendering

Rendering SHOULD be asynchronous.

Possible outputs:

- audio snippet;
- video snippet;
- captioned vertical video;
- square social card/video;
- waveform animation;
- static image.

Do not generate every format by default.

Generate on demand or according to product usage patterns.

### 11.5 Deep links

Every shareable clip MUST link back to:

- original episode;
- appropriate timestamp;
- source show;
- access/subscription page if required.

The clip should be an acquisition surface, not a content dead end.

### 11.6 Transcript captions

Where transcripts exist:

- captions should be derived from canonical timed transcript data;
- speaker labels should be preserved where available;
- users/creators may correct text before final render where policy permits.

### 11.7 Copyright and permissions

The clip service MUST enforce creator/platform permissions.

Do not assume every external RSS feed permits derivative clipping.

For external content, disable public clip rendering unless terms and product policy explicitly allow it.

### 11.8 Abuse controls

Apply:

- rate limits;
- quotas;
- moderation;
- public-visibility restrictions;
- report/takedown flow;
- audit logs for creator/admin actions.

---

## 12. QUOTE CARDS

### 12.1 Objective

Create a low-cost sharing mechanism from transcript text.

### 12.2 Quote selection

Users may select transcript text within bounded limits.

A quote card should include:

- quote;
- speaker when known;
- show;
- episode;
- timestamp;
- brand attribution;
- deep link or QR representation where appropriate.

### 12.3 Canonical linkage

A quote MUST reference:

- transcript segment IDs;
- episode;
- timestamp.

Do not store only copied text without provenance.

### 12.4 Rendering

Static image rendering should be asynchronous only if rendering cost warrants it.

A lightweight synchronous template render MAY be acceptable if benchmarked and bounded.

### 12.5 Acceptance criteria

- quote links seek to the correct timestamp;
- transcript edits can be reconciled;
- inaccessible premium text is not exposed beyond permitted preview rules;
- malicious text does not produce injection vulnerabilities.

---

## 13. VIDEO PODCASTS AND MEDIA VARIANTS

### 13.1 Objective

Support one episode with multiple playable representations while preserving one canonical episode/content model.

Do NOT create a parallel `VideoEpisode` hierarchy unless an ADR proves a fundamentally different product requirement. Audio, video, captions, thumbnails, waveforms, previews, clips, and other derivatives are media assets/variants attached to canonical content.

### 13.2 Canonical media model

An episode may have variants such as:

```text
AUDIO_MASTER
AUDIO_HIGH
AUDIO_STANDARD
AUDIO_DATA_SAVER
VIDEO_MASTER
VIDEO_1080
VIDEO_720
VIDEO_480
VIDEO_ADAPTIVE
SUBSCRIBER_AUDIO
SUBSCRIBER_VIDEO
CAPTION
THUMBNAIL
WAVEFORM
PREVIEW
```

The taxonomy MUST remain extensible and MUST NOT be hard-coded across clients.

Conceptual fields:

```text
MediaAsset
    id
    provider
    provider_product
    provider_resource_id_or_object_key
    bucket_or_library optional
    media_type
    checksum
    byte_size
    source_asset_id
    storage_class
    status
    created_at

MediaVariant
    id
    episode_id
    asset_id
    kind
    codec
    container
    bitrate
    width
    height
    duration_ms
    language
    access_class
    processing_version
    status
```

`MediaAsset` represents a stored/managed object. `MediaVariant` represents how that asset participates in playback or presentation. The exact repository implementation may combine these concepts only if ownership, lifecycle, provenance, and provider portability remain explicit.

Provider-specific IDs MUST be isolated inside provider-facing fields/adapters. Core episode/business logic MUST NOT depend directly on a Cloudflare, AWS, Mux, or other vendor identifier.

### 13.3 Position synchronisation

Switching audio ↔ video MUST preserve playback position.

The canonical position is media timeline time, not elapsed wall-clock time. Transcripts, chapters, bookmarks, analytics, clips, and football event markers MUST all resolve against the same canonical timeline.

### 13.4 Processing pipeline

Media ingestion should support an asynchronous, resumable pipeline such as:

```text
Upload requested
  ↓
Direct-to-provider upload
  ↓
Upload completed event/webhook
  ↓
Validation / malware or policy checks
  ↓
Probe / metadata extraction / checksum
  ↓
Transcode or normalise where required
  ↓
Audio extraction where required
  ↓
Thumbnail / artwork derivatives
  ↓
Waveform
  ↓
Transcript / captions
  ↓
Chapters
  ↓
Entity extraction
  ↓
Publish-ready
```

Each stage MUST be observable, idempotent, retryable where safe, cancellable where practical, and capable of representing partial success.

Large media upload/download bytes MUST NOT transit through Django application workers merely to reach object storage or a video platform. The application should authorise the operation and issue a short-lived upload/download capability; the client should transfer directly to the storage/media provider when supported.

### 13.5 Audio delivery

Audio delivery should prefer a small, intentional set of delivery variants instead of generating unnecessary renditions.

Typical policy MAY include:

- retained creator/master source;
- normal/high-quality delivery variant;
- bandwidth-efficient/data-saver variant;
- optional preview/clip derivative.

Do not multiply storage cost by creating variants without a measured playback or product requirement.

### 13.6 Video delivery

Prefer adaptive streaming for video at scale. Raw creator originals MUST NOT be the default public playback path.

The current production implementation MUST use Cloudflare Stream through `pycflare` for managed video direct creator upload, resumable/TUS provisioning, encoding/transcoding, adaptive playback, thumbnails, captions where applicable, and signed/private playback. SANFootball MUST still depend on a canonical `VideoPlatform` abstraction so a later provider migration does not rewrite episode/domain models. Domain/application code MUST NOT call `pycflare.media.StreamClient` directly outside the Cloudflare video adapter.

A future self-hosted implementation MAY use FFmpeg/GStreamer and object storage/CDN infrastructure, but this must be introduced only when cost, custom processing, compliance, codec control, or scale justifies the operational burden.

### 13.7 Media storage and delivery boundary

Application compute MUST NOT be the media origin of record.

Use object storage and CDN/media-delivery infrastructure for:

- audio;
- images/artwork;
- thumbnails;
- transcripts and captions;
- waveform data;
- downloadable attachments;
- original/source media where policy allows;
- processed media not delegated to a managed video provider.

The current production implementation MUST use Cloudflare R2 through `pycflare` for audio, arbitrary durable binary assets, source files, downloadable attachments, captions/transcript files, waveforms, and processed assets not delegated to Cloudflare Stream. User-facing artwork/photograph upload and delivery MUST use Cloudflare Images through `pycflare`; R2 remains the Cloudflare-backed home for source/archive images and arbitrary image objects that are not intended for managed Images delivery. Public R2 delivery MUST use a Cloudflare custom domain/edge path. Portability remains mandatory behind the canonical storage/media adapters; equivalent providers are migration targets, not parallel active implementations.

### 13.8 Direct uploads

Creator uploads MUST be designed for direct-to-storage/provider transfer.

Required flow:

```text
Client requests upload intent
        ↓
Application authenticates + authorises + validates quota/policy
        ↓
Application creates upload session / presigned URL / one-time provider URL
        ↓
Client uploads directly to storage/video provider
        ↓
Provider completion callback or verified client completion
        ↓
Application records canonical asset + emits processing event
```

Requirements:

- use multipart/resumable upload for large or unreliable transfers where supported;
- use short-lived credentials/URLs;
- scope permission to the exact object/upload operation;
- enforce maximum size/duration/format/quota before or during processing;
- never expose provider API secrets to clients;
- abort or garbage-collect incomplete uploads;
- make upload completion idempotent;
- treat provider callbacks/webhooks as untrusted until authenticated and validated;
- user-facing image upload intents MUST use `pycflare` Cloudflare Images Direct Creator Upload; source/archive/non-managed image objects MAY use R2 behind the canonical storage adapter; the browser uploads directly to the issued Cloudflare capability;
- audio/general R2 upload intents MUST use the `pycflare` R2 integration, normally a presigned upload capability for bounded direct object upload and a resumable/multipart strategy for large or unreliable transfers where the selected client flow supports it;
- video upload intents MUST be provisioned through `pycflare` Cloudflare Stream direct creator upload or TUS provisioning, using TUS whenever the package/Cloudflare rules require it or resumability is appropriate;
- the backend MUST validate the provider object/resource after upload before marking the canonical `MediaAsset` authoritative.

### 13.9 Premium/private media

Premium or private media MUST be enforced twice:

1. the application authorises access using the canonical entitlement/access policy;
2. the media provider/CDN receives only a short-lived signed playback/download capability.

Django MUST NOT proxy the entire media stream merely to enforce subscription access.

Persistent public URLs MUST NOT be emitted for protected assets when doing so would bypass entitlement checks.

This rule applies to **images as well as audio/video**. Premium artwork, private creator/team imagery, member-only posters/thumbnails, private clips, and any visual asset whose disclosure is itself gated MUST not be exposed through a permanently public Cloudflare Images/R2 URL. The backend MUST either return an approved public teaser/placeholder or an expiring signed image capability after AccessPolicy succeeds.

### 13.10 Source immutability and provenance

Original/source assets SHOULD be immutable after successful ingestion. Replacements should create a new version or asset lineage rather than silently mutating the underlying source.

Track:

- source checksum;
- processing pipeline version;
- derivative parent/source;
- provider;
- creation time;
- relevant codec/container metadata;
- retention/storage policy.

### 13.11 Acceptance criteria

- audio/video switching preserves canonical position;
- media entitlement is enforced at application and delivery layers;
- creator uploads can bypass application-server byte transport;
- large upload resumability is supported where required;
- processing failures are recoverable and observable;
- clients can choose lower-quality/data-saver playback;
- source assets are immutable or versioned;
- provider-specific details do not leak into domain logic;
- temporary uploads and intermediate derivatives are lifecycle-managed;
- a provider migration can be implemented without replacing episode/domain models.

## 14. SEMANTIC TRANSCRIPT SEARCH — "ASK SANFOOTBALL"

### 14.1 Objective

Allow users to ask football-specific questions and receive grounded podcast moments rather than opaque AI answers.

### 14.2 Core principle: retrieval before generation

The product MUST prioritise grounded retrieval.

A query such as:

```text
What did our analysts say about Osimhen joining Chelsea?
```

should return:

- relevant episodes;
- exact transcript segments;
- timestamps;
- show/creator attribution;
- optional concise synthesis grounded in retrieved segments.

The user MUST be able to jump directly to source audio.

### 14.3 Indexing

Index semantic units such as:

- transcript segments;
- chapter summaries;
- episode summaries;
- clip transcripts;
- entity-linked moments.

Avoid indexing enormous transcripts as a single vector.

### 14.4 Metadata filters

Semantic retrieval should support filtering by:

- show;
- date range;
- club;
- player;
- competition;
- creator;
- content access;
- language;
- episode.

### 14.5 Access control

Semantic search MUST NOT leak premium or private transcript material.

Retrieval must filter by entitlement before exposing text.

If a premium result is discoverable as a teaser, the teaser must follow access-policy rules.

### 14.6 Grounding

Generated answers, if enabled, MUST include internal source references sufficient for the UI to present:

```text
Episode
Timestamp
Transcript excerpt
```

Do not present unsupported hallucinated claims as if the podcast said them.

### 14.7 AI-provider independence

The domain must not be tightly coupled to one embedding or language-model provider.

Use provider adapters.

Persist provider/model/version metadata for reproducibility where appropriate.

### 14.8 Cost controls

Support:

- batching;
- deduplication;
- incremental re-indexing;
- content-hash change detection;
- usage limits;
- cache where appropriate;
- model selection by task.

---

## 15. FOOTBALL ENTITY EXTRACTION AND CONTENT KNOWLEDGE GRAPH

### 15.1 Objective

Connect podcast moments to football entities.

### 15.2 Entity types

At minimum, design for:

- club;
- player;
- manager;
- competition;
- fixture/match;
- topic.

Future types may include:

- stadium;
- referee;
- national team;
- transfer;
- award.

### 15.3 Entity mention

Conceptual relation:

```text
EntityMention
    id
    entity_type
    entity_id
    episode_id
    transcript_segment_id
    start_ms
    end_ms
    confidence
    source
    review_status
```

### 15.4 Extraction

Entity extraction MUST be asynchronous and may combine:

- deterministic alias matching;
- canonical football data;
- NER;
- contextual disambiguation;
- human review.

Do not rely solely on fuzzy string matching.

Example ambiguity:

```text
United
City
Ronaldo
PSG
```

requires context.

### 15.5 Alias system

Football entities need controlled aliases.

Example:

```text
Manchester United
Man United
Man Utd
MUFC
```

Aliases must be centrally managed.

Do not create per-feature alias maps.

### 15.6 Human corrections

Creator/editor corrections SHOULD override automated extraction.

Record provenance and maintain correction durability when reprocessing.

### 15.7 Knowledge-driven experiences

Entity links should enable:

- entity episode pages;
- latest mentions;
- popular clips;
- timestamped mentions;
- related shows;
- trending topics;
- notification triggers;
- smart playlists;
- personalised home feed;
- match collections.

---

## 16. FOLLOW CLUBS, PLAYERS, COMPETITIONS, CREATORS, AND TOPICS

### 16.1 Objective

Expand "following" beyond podcast shows.

### 16.2 Follow target abstraction

Implement a canonical follow/subscription abstraction where appropriate rather than a separate follow table per entity type.

The agent must choose a model that:

- preserves referential integrity as much as practical;
- supports efficient queries;
- avoids unrestricted generic relations if they cause operational problems;
- supports future target types.

### 16.3 Followed targets

Support:

- show;
- creator;
- network/channel;
- club;
- player;
- manager;
- competition;
- topic.

### 16.4 Effects

Following MAY influence:

- home feed;
- inbox;
- recommendations;
- notifications;
- smart playlists;
- live-room suggestions;
- annual recap.

Following MUST NOT silently grant premium entitlement.

---

## 17. INTELLIGENT NOTIFICATIONS

### 17.1 Objective

Notify users about personally relevant football audio events without producing notification fatigue.

### 17.2 Notification triggers

Potential triggers:

- new episode from followed show;
- new content mentioning followed club/player;
- new creator content;
- premium episode release;
- early-access release;
- live room starting;
- matchday room starting;
- reply to comment;
- poll result;
- clip engagement if relevant to creator;
- subscription/payment event;
- download completed where client supports local notification.

### 17.3 Preference hierarchy

Support:

- global channel preference;
- notification category;
- followed-target overrides;
- quiet hours;
- digest mode where appropriate.

### 17.4 Delivery channels

Architect for adapters:

- in-app;
- email;
- push;
- optional SMS/other channels only when product requires them.

Do not couple notification creation directly to a specific provider.

### 17.5 Fan-out

Large fan-out MUST be asynchronous and batched.

Do not send thousands of messages inside the publishing transaction.

### 17.6 Deduplication

A single event should not generate duplicate notifications because the user follows both:

```text
Arsenal
```

and:

```text
Premier League
```

when one episode satisfies both.

Record matched reasons separately if useful.

---

## 18. HIGHLIGHTS DISCOVERY FEED

### 18.1 Objective

Use short-form media for discovery without turning the product into an unrelated infinite-video platform.

### 18.2 Feed item

A highlight should normally be a canonical clip with:

- source episode;
- creator;
- duration;
- transcript/caption;
- relevant entities;
- engagement;
- deep link.

### 18.3 Ranking

Ranking may consider:

- followed entities;
- listening history;
- source episode relevance;
- clip completion;
- saves;
- shares;
- hides;
- freshness;
- editorial boost;
- diversity.

### 18.4 Guardrails

Avoid:

- unbounded autoplay media downloads;
- excessive bandwidth use;
- repetitive clips from one show;
- ranking solely by raw engagement;
- exposing premium source content beyond allowed preview.

---

## 19. CREATOR ANALYTICS

### 19.1 Objective

Give creators actionable insight into audience behaviour.

### 19.2 Raw analytics event architecture

Do not calculate every metric directly from transactional playback rows at request time.

Use an event model capable of supporting aggregation.

Possible events:

- impression;
- episode_view;
- play_start;
- playback_heartbeat;
- seek;
- chapter_start;
- pause;
- resume;
- completion;
- download_request;
- download_complete;
- clip_view;
- clip_share;
- quote_share;
- follow;
- unfollow;
- premium_preview;
- subscription_page_view;
- conversion.

### 19.3 Listening metrics

Creator dashboard should support:

- unique listeners;
- starts;
- engaged listeners;
- completion rate;
- average consumption;
- listening time;
- new listeners;
- returning listeners;
- follower growth;
- subscribers attributable to content;
- device/media-type breakdown where privacy permits.

### 19.4 Retention curve

Support retention by media timeline.

Do not treat a 2x listener as if they consumed only half the content.

### 19.5 Drop-off detection

Batch analytics may identify:

- abnormal exit points;
- long ad-related drop-off;
- intro abandonment;
- segment-specific exits.

These MUST be presented as analytics signals, not guaranteed causal claims.

Use wording such as:

```text
Listener drop-off increased near 08:42.
```

not:

```text
Your advertisement caused listeners to leave.
```

unless the relationship is actually known.

### 19.6 Replay hotspots

Detect repeated seeks/replays.

These may feed:

- creator insight;
- highlight suggestions;
- chapter quality review.

### 19.7 Privacy

Do not expose individual listener identities unnecessarily.

Creator analytics should default to aggregate data.

Apply thresholds for sensitive small cohorts where appropriate.

---

## 20. SUBSCRIPTION CONVERSION ANALYTICS

Track funnels such as:

```text
Anonymous → Registered
Registered → Engaged Listener
Engaged Listener → Subscription Page
Subscription Page → Trial
Trial → Paid
Paid → Renewed
Paid → Cancelled
```

Content-specific attribution may include:

```text
Episode → Premium Preview
Premium Preview → Offer
Offer → Checkout
Checkout → Subscriber
```

### 20.1 Attribution

Define attribution windows and models.

Do not present arbitrary conversion attribution as absolute causality.

### 20.2 Entitlement analytics

Measure:

- premium starts;
- locked-content views;
- preview completion;
- ad-free variant usage;
- early-access usage;
- member-only live-room attendance.

---

## 21. AD-FREE AND PREMIUM MEDIA VARIANTS

### 21.1 Objective

Use the canonical media and entitlement architecture rather than dynamic hacks.

An episode MAY have:

```text
free media variant
subscriber ad-free variant
premium video variant
data-saver variant
```

### 21.2 Selection

Media selection is a server-authorised decision based on:

- episode;
- user;
- entitlement;
- device capability;
- requested quality;
- network preference;
- availability.

### 21.3 Do not expose premium URLs

The client may learn which variant is selected, but permanent protected storage URLs must not become a bypass around access policy.

---

## 22. PODCAST NETWORKS / CHANNELS

### 22.1 Objective

Allow multiple shows under a shared creator/brand organisation.

Conceptual model:

```text
Network
    ├── Show A
    ├── Show B
    ├── Show C
```

### 22.2 Capabilities

Networks may support:

- branding;
- multiple shows;
- network page;
- network follow;
- network membership;
- network-wide subscription;
- team permissions;
- aggregate analytics;
- bundled premium access.

### 22.3 Entitlements

Do not duplicate subscription logic.

A network plan should grant canonical entitlements to qualifying resources.

---

## 23. CREATOR TEAMS AND ROLE-BASED ACCESS

### 23.1 Objective

Support professional creator organisations.

Possible roles:

- Owner;
- Administrator;
- Producer;
- Editor;
- Host;
- Moderator;
- Analyst;
- Billing Manager.

### 23.2 Permission model

Do not hard-code role checks throughout views.

Use capabilities/permissions.

Example capabilities:

```text
show.edit
episode.publish
episode.media.manage
transcript.edit
clip.publish
comments.moderate
analytics.view
billing.manage
team.manage
network.manage
live.host
```

Roles map to capabilities.

### 23.3 Security

High-risk actions should require:

- authenticated session;
- permission check;
- audit log;
- optional re-authentication for billing or ownership changes.

### 23.4 Ownership transfer

Ownership transfer MUST be explicit, audited, and protected against accidental lockout.

---

## 24. LIVE PODCASTING

### 24.1 Objective

Allow live football audio to become durable podcast content.

### 24.2 Broadcast lifecycle

Conceptual state machine:

```text
DRAFT
  ↓
SCHEDULED
  ↓
LIVE
  ↓
ENDING
  ↓
PROCESSING
  ↓
PUBLISHED
```

Failure/cancellation states should be explicit.

### 24.3 Live room capabilities

May support:

- host;
- co-host;
- listeners;
- request to speak;
- live comments;
- reactions;
- polls;
- moderators;
- member-only access;
- recording.

### 24.4 Media infrastructure

The application domain should not pretend to be the media server if live media is handled by specialised real-time infrastructure.

Keep clear separation between:

- room domain;
- authentication;
- permissions;
- signalling/session metadata;
- actual media transport;
- recording;
- post-processing.

### 24.5 Live to episode conversion

A completed broadcast should be capable of becoming a normal episode:

```text
LiveBroadcast
      ↓
Recording
      ↓
Episode
      ↓
MediaVariant
      ↓
Transcript
      ↓
Chapters
      ↓
Summary
      ↓
Entity Mentions
      ↓
Highlights
```

Do not create a permanently separate on-demand content ecosystem for completed live streams.

### 24.6 Failure handling

Recording finalisation MUST support retries.

A failed transcript must not prevent the episode from existing if media is valid.

A failed highlight-generation job must not block publication.

---

## 25. MATCHDAY ROOMS

### 25.1 Objective

Build a football-native community experience around fixtures.

### 25.2 Fixture linkage

A matchday room MUST link to the canonical fixture entity.

Possible phases:

```text
PRE_MATCH
LIVE_MATCH
POST_MATCH
ARCHIVED
```

### 25.3 Content around a fixture

The fixture page may aggregate:

- preview episodes;
- starting-lineup reaction;
- live room;
- polls;
- post-match reaction;
- tactical analysis;
- player ratings;
- clips;
- related transcript moments.

### 25.4 Match data

If external sports-data providers are used:

- isolate provider adapters;
- store provider IDs separately from internal IDs;
- define data ownership;
- respect licensing;
- tolerate provider outages;
- avoid putting provider-specific payloads directly into core domain logic.

---

## 26. MATCH-AWARE PODCAST CHAPTERS

### 26.1 Objective

Link podcast chapters to football events and entities.

Example:

```text
00:00 Introduction
04:20 Tactical setup
13:44 Arsenal first goal
21:17 Chelsea equaliser
35:01 Second-half changes
47:31 Saka analysis
56:02 Player ratings
```

### 26.2 Chapter enrichment

A chapter may reference:

- fixture;
- club;
- player;
- manager;
- competition;
- match event.

Keep chapter editorial text distinct from football-event data.

### 26.3 Match-event alignment

Automated alignment MUST expose confidence and permit correction.

Do not silently claim a transcript timestamp exactly corresponds to a match event when uncertain.

---

## 27. "LISTEN AROUND THE MATCH" COLLECTIONS

### 27.1 Objective

Create dynamically assembled listening journeys around fixtures.

A collection may contain:

```text
Preview
Starting XI Reaction
Live/Post-match Reaction
Tactical Breakdown
Player Ratings
Transfer/Follow-up Discussion
```

### 27.2 Collection type

Prefer a reusable collection/playlist projection over creating copied episode records.

Match collections may be:

- dynamic;
- editorially curated;
- hybrid.

### 27.3 Queue integration

A user may choose:

```text
Play Match Collection
```

which populates or temporarily layers onto the canonical queue.

Do not create another playback queue.

---

## 28. PERSONALISED FOOTBALL HOME

### 28.1 Objective

Make the home screen reflect the listener's football interests.

Possible modules:

- continue listening;
- followed clubs;
- followed players;
- followed competitions;
- new from followed shows;
- matchday;
- recommended episodes;
- trending discussions;
- live now;
- premium;
- downloaded for you;
- creator highlights.

### 28.2 Feed architecture

Home modules should use a feed-composition layer.

Avoid one gigantic controller/view with dozens of independent queries.

Consider:

- bounded module loaders;
- caching;
- parallel async I/O where framework permits;
- precomputed recommendation candidates;
- fallbacks;
- personalised ranking.

### 28.3 Cold start

For new users, derive a useful feed from:

- onboarding football interests;
- popular content;
- editorial content;
- location/language only where appropriate and consented.

---

## 29. LISTENER PROFILE AND LISTENING STATISTICS

### 29.1 Objective

Give listeners useful, shareable insight into their habits.

Potential metrics:

- minutes listened;
- episodes started;
- episodes completed;
- completion rate;
- most-listened show;
- most-listened creator;
- most-listened club;
- most-listened player;
- most-listened competition;
- favourite listening period;
- longest listening streak;
- live rooms attended.

### 29.2 Privacy

Listener analytics are private by default.

If public profile statistics are introduced, users MUST explicitly control visibility.

---

## 30. ANNUAL "YOUR SANFOOTBALL YEAR" RECAP

### 30.1 Objective

Create a football-specific annual engagement and sharing experience.

Possible recap facts:

- total minutes;
- favourite club;
- favourite player/topic;
- top show;
- top episode;
- transfer-rumour listening;
- live-room participation;
- completion rate;
- longest listening day;
- favourite competition.

### 30.2 Architecture

Annual recap should be generated from analytics aggregates, not by running enormous ad hoc queries during page load.

Use a versioned recap snapshot.

Example:

```text
ListenerRecap
    user_id
    year
    version
    generated_at
    payload
```

### 30.3 Regeneration

Support deterministic regeneration when analytics corrections materially change results.

---

## 31. TASTEFUL ACHIEVEMENTS

### 31.1 Objective

Reward meaningful engagement without making the product feel childish or manipulative.

Potential achievements:

- Founding Listener;
- 100 Episodes;
- 500 Listening Hours;
- Matchday Regular;
- Live Room Regular;
- Early Supporter;
- Long-Term Member.

Avoid aggressive dark-pattern streak mechanics.

### 31.2 Rules

Achievement evaluation should be:

- deterministic;
- idempotent;
- versioned;
- auditable.

Do not embed reward logic in random playback endpoints.

---

## 32. CONNECTED DEVICES, CASTING, AUTOMOTIVE, AND TV

### 32.1 Objective

Make listening available in contexts where audio naturally happens.

Architect for:

- Chromecast;
- AirPlay;
- Android Auto;
- CarPlay;
- smart speakers;
- television;
- wearables.

Implementation order should follow actual client strategy.

### 32.2 Core requirement

Connected devices MUST reuse:

- canonical playback session;
- canonical queue;
- canonical progress;
- canonical entitlement.

Do not create device-specific duplicate listening state.

### 32.3 Remote playback

If remote-control capability is implemented:

- authenticate commands;
- scope devices to user;
- protect against replay;
- handle disconnected devices;
- require explicit user intent where appropriate.

---

## 33. LOW-BANDWIDTH AND DATA-SAVER MODE

### 33.1 Objective

Treat constrained mobile connectivity as a primary product scenario.

### 33.2 Media variants

Provide lower-bitrate audio variants where cost-effective.

Example conceptual levels:

```text
HIGH
STANDARD
DATA_SAVER
```

Exact codec/bitrate decisions must be based on quality testing.

### 33.3 Policy

Users may choose:

- always high quality;
- automatic;
- data saver on mobile;
- audio-only on mobile data;
- Wi-Fi-only video;
- Wi-Fi-only automatic downloads.

### 33.4 API design

Clients should request capability/quality preference, not construct storage URLs.

The media-selection service chooses an authorised compatible variant.

---

## 34. TRANSCRIPT ACCESSIBILITY AND TRANSLATION

### 34.1 Core transcript experience

Support:

- speaker labels;
- timed text;
- word/segment highlighting;
- tap-to-seek;
- search;
- copy;
- share;
- quote creation;
- adjustable text size;
- high-contrast compatible UI;
- keyboard navigation on web;
- screen-reader semantics.

### 34.2 Translation

Architect for transcript translation.

Translations MUST:

- reference the canonical transcript;
- record language;
- record source transcript version;
- record provider/model/version where generated;
- support human correction;
- invalidate/reprocess when canonical source changes materially.

### 34.3 Nigerian and international languages

The architecture should not hard-code only one or two languages.

It should be capable of adding languages such as:

- English;
- French;
- Spanish;
- Arabic;
- Hausa;
- Yoruba;
- Igbo;

and others without schema redesign.

### 34.4 Accessibility

Accessibility MUST be tested, not merely stated.

Web interfaces should target current WCAG AA expectations where applicable.

---

## 35. CREATOR-SIDE AI ASSISTANCE

### 35.1 Objective

Use AI to reduce publishing effort while preserving creator control.

Potential generated drafts:

- episode titles;
- descriptions;
- chapter titles;
- show notes;
- social copy;
- key quotes;
- clip candidates;
- topics;
- entity suggestions;
- SEO metadata;
- summary.

### 35.2 Approval requirement

AI-generated metadata is a DRAFT by default.

Do not silently publish AI changes.

### 35.3 Provenance

Where appropriate, record:

- generation time;
- model/provider;
- source version;
- creator edits;
- approval state.

### 35.4 Safety

AI assistance must not:

- fabricate transcript quotations;
- invent football facts and present them as episode content;
- overwrite creator-authored metadata without approval;
- leak premium/private content to unauthorised providers contrary to policy.

---

## 36. API DESIGN PRINCIPLES

### 36.1 Resource consistency

Use consistent representations across:

- episodes;
- clips;
- playlists;
- playback sessions;
- follows;
- notifications;
- live rooms;
- networks.

### 36.2 Pagination

Use cursor pagination for large or frequently changing feeds where appropriate.

Offset pagination MAY remain acceptable for small/admin lists.

### 36.3 Idempotent mutation endpoints

Provide idempotency where duplicate client requests are likely:

- queue insertion;
- follow;
- download request;
- clip creation;
- checkout/webhook operations;
- live-room join intent;
- import job creation.

### 36.4 Conditional requests and caching

Use ETag/Last-Modified/cache headers where appropriate for:

- episode metadata;
- transcripts;
- artwork;
- public show pages;
- RSS output;
- static discovery modules.

Do not cache personalised protected content across users.

### 36.5 Error format

Use a stable error envelope.

Errors should be:

- machine-readable;
- human-debuggable;
- safe for clients;
- correlated with logs.

Do not return raw stack traces in production.

---

## 37. INTERNAL EVENTS

The platform should use explicit domain/application events to decouple workflows.

Possible events:

```text
episode.published
episode.updated
media.ready
transcript.ready
chapters.ready
entity_mentions.ready
clip.created
clip.rendered
show.followed
entity.followed
playback.completed
live.started
live.ended
live.recording_ready
subscription.activated
subscription.cancelled
entitlement.changed
```

### 37.1 Event rules

Events MUST:

- have stable schemas;
- carry identifiers, not enormous object dumps;
- be idempotently consumable;
- include event ID;
- include occurred-at timestamp;
- include schema/version when necessary.

### 37.2 Transactional consistency

Where event publication must correspond to committed database state, use an outbox pattern or equivalent safe mechanism.

Do not publish an external event before a transaction commits when that could create inconsistent consumers.

---

## 38. BACKGROUND JOB ARCHITECTURE

### 38.1 Job categories

Classify jobs:

- latency-sensitive;
- ordinary;
- CPU-heavy;
- media-heavy;
- bulk;
- scheduled;
- low-priority.

Use separate queues/pools where workload characteristics differ. At minimum, the architecture SHOULD allow independent scaling for:

```text
web/api
ordinary workers
media/audio workers
video/media-orchestration workers
AI/transcription workers
notification workers
bulk/backfill workers
scheduled jobs
```

Do not allow video transcoding, waveform generation, backfills, or AI processing to starve subscription, entitlement, notification, or security-sensitive work.

### 38.2 Retry policy

Retries MUST be bounded and use exponential backoff with jitter where appropriate.

Differentiate:

- transient failure;
- permanent validation failure;
- provider rejection;
- rate limit;
- timeout;
- resource exhaustion;
- duplicate delivery;
- cancelled work.

A retry MUST NOT create duplicate media variants, duplicate notifications, duplicate subscriptions, duplicate billing actions, or duplicate analytics aggregation.

### 38.3 Dead-letter handling

Permanent/exhausted failures must be observable and recoverable.

Provide admin/operator tooling to:

- inspect failed jobs/messages;
- inspect the last exception and retry history;
- retry safe failures;
- redrive dead-lettered work;
- cancel/abandon invalid work;
- view correlation IDs;
- view source resource;
- view provider response where safe;
- identify poison messages.

### 38.4 Progress

Long-running jobs should expose meaningful progress where practical.

Examples:

- OPML import;
- media upload finalisation;
- media processing;
- transcript processing;
- backfills;
- recap generation.

### 38.5 Autoscaling signals

Worker autoscaling SHOULD use workload-aware signals rather than CPU alone.

Examples:

```text
queue depth
oldest message age
backlog per worker
median/p95 processing duration
concurrency saturation
provider rate-limit budget
CPU / memory for compute-heavy pools
```

Web/API compute SHOULD scale independently using request concurrency, latency, CPU, memory, or load-balancer request metrics.

### 38.6 Backpressure

Every high-volume producer/consumer path MUST define backpressure behaviour.

When downstream capacity is saturated:

- queue rather than overload;
- reject or defer low-priority work before critical work;
- respect provider rate limits;
- cap concurrent transcodes/processes;
- prevent unbounded in-memory buffering;
- expose saturation metrics and alerts.

### 38.7 Resource isolation

CPU-heavy or memory-heavy jobs SHOULD have explicit resource limits and MUST NOT execute in the same process pool as latency-sensitive API work.

FFmpeg/GStreamer/subprocess execution MUST use:

- bounded concurrency;
- timeouts;
- temporary-disk quotas;
- subprocess exit-code handling;
- cleanup in failure paths;
- structured progress/error reporting.

### 38.8 Broker independence

The application MAY use Celery or the repository's existing task/event infrastructure, but domain logic MUST NOT depend directly on a single broker implementation.

Where the repository already has a canonical broker/event abstraction, extend it rather than introducing another parallel queueing system.

## 39. SEARCH ARCHITECTURE

### 39.1 Search layers

SanFootball may have:

1. metadata search;
2. transcript lexical search;
3. semantic transcript search;
4. football entity search.

These are complementary, not duplicate products.

### 39.2 Canonical search facade

Clients should preferably consume a unified search service capable of federating results.

Do not expose infrastructure-specific query syntax to clients.

### 39.3 Ranking

Search ranking should consider:

- textual relevance;
- semantic relevance;
- recency;
- popularity;
- follows;
- entity relevance;
- editorial signals;
- entitlement visibility.

---

## 40. RECOMMENDATION ARCHITECTURE

The recommendation system should build on canonical listener and football signals.

Potential signals:

- followed shows;
- followed entities;
- listening history;
- completion;
- skips;
- replays;
- saves;
- queue additions;
- shares;
- clips;
- live-room attendance;
- subscriptions;
- explicit hides/dislikes.

### 40.1 Negative signals

Support explicit "not interested" or hide signals.

Do not assume all clicks are positive preference.

### 40.2 Explainability

Where practical, the UI may explain:

```text
Because you follow Arsenal
Because you listened to Transfer Talk
Trending in Premier League
```

### 40.3 Cold start

Use:

- onboarding interests;
- editorial;
- trending;
- location/language only when appropriate.

---

## 41. COMMERCIAL AND ENTITLEMENT RULES

### 41.1 AccessPolicy remains canonical

All premium capabilities must route through the existing canonical policy.

Examples:

- premium episode;
- early-access episode;
- ad-free media;
- private RSS;
- premium video;
- premium transcript;
- member-only clip;
- live room;
- network bundle.

### 41.2 Do not encode plan names throughout product logic

Prefer capabilities/entitlements.

Bad:

```python
if user.plan == "gold":
```

Preferred conceptual approach:

```python
access_policy.can(user, "episode.ad_free", resource=episode)
```

Exact API should fit existing codebase conventions.

### 41.3 Subscription state

Payment provider state is not automatically identical to domain subscription state.

Webhook processing must be:

- authenticated;
- idempotent;
- audited;
- resilient to out-of-order delivery.

---

## 42. SECURITY REQUIREMENTS

### 42.1 Threat modelling

Before implementing high-risk features, create lightweight threat models for:

- RSS URL fetching;
- media uploads;
- premium media delivery;
- creator team management;
- clip sharing;
- live rooms;
- semantic search;
- AI provider integration;
- external sports data;
- payment webhooks;
- connected-device control.

### 42.2 Upload security

Validate:

- content type;
- extension;
- magic bytes;
- size;
- duration where relevant;
- decompression/archive hazards;
- malware scanning strategy where warranted.

Do not trust client-provided MIME type.

### 42.3 Rate limiting

Rate limit:

- authentication-sensitive operations;
- RSS imports;
- clip generation;
- AI generation;
- semantic search;
- public share creation;
- comments/reactions;
- live join requests;
- password/reset flows;
- creator invites.

### 42.4 Secrets

Secrets MUST:

- come from secure configuration;
- never be committed;
- never appear in client bundles;
- never be logged.

### 42.5 Audit logging

Audit at minimum:

- ownership changes;
- team membership changes;
- permission changes;
- episode publication/unpublication;
- premium entitlement administrative overrides;
- billing operations;
- moderation actions;
- destructive creator actions.

### 42.6 Data deletion

User deletion workflows must consider:

- playback history;
- follows;
- comments;
- analytics;
- clips;
- creator-owned content;
- subscriptions;
- legal/accounting retention;
- anonymisation where appropriate.

---

## 43. PRIVACY REQUIREMENTS

Analytics and personalisation are not justification for collecting unlimited behavioural data.

The agent should document:

- what is collected;
- why;
- retention;
- access;
- aggregation;
- deletion/anonymisation.

Avoid storing unnecessarily precise device or location information.

Do not expose listener-level analytics to creators unless explicitly designed, justified, and consented.

---

## 44. PERFORMANCE AND SCALABILITY REQUIREMENTS

### 44.1 Target philosophy

Set measurable SLOs from production telemetry rather than arbitrary optimism.

The architecture MUST optimise the system by workload class instead of assuming one server tier solves every bottleneck.

Implementation should aim for:

- bounded query counts;
- responsive feed and playback-control APIs;
- asynchronous heavy processing;
- direct-to-object-storage/media-provider uploads;
- CDN/edge-served media and static assets;
- cacheable public metadata;
- minimal origin bandwidth for playback;
- batched analytics;
- connection pooling;
- backpressure;
- horizontal scaling of stateless application compute;
- independent scaling of worker pools.

### 44.2 Stateless application compute

Web/API instances MUST be disposable and replaceable.

Do not depend on local instance disk for durable:

- uploads;
- user files;
- media;
- sessions;
- queue state;
- generated artefacts that cannot be recreated;
- application source of truth.

Local disk MAY be used only for bounded temporary work with explicit cleanup.

### 44.3 Database indexing

Review indexes for:

- user + progress;
- user + queue order;
- user + follow target;
- episode publication time;
- show + publication time;
- entity mention + entity;
- entity mention + episode;
- transcript search;
- notification status;
- analytics event partition keys;
- live room + fixture;
- creator team membership;
- media asset/variant status;
- processing-job lookup keys.

Do not add indexes blindly; verify write/read trade-offs and realistic cardinality.

### 44.4 Query plans

For high-volume paths, inspect query plans against realistic datasets and production-like cardinalities.

Load/performance tests SHOULD include:

- home/discovery feeds;
- episode detail;
- queue/progress updates;
- subscription/entitlement checks;
- search;
- creator analytics reads;
- media-selection endpoints;
- upload-intent creation.

### 44.5 Database connections

The platform MUST prevent application scaling from exhausting PostgreSQL connections.

Use connection pooling such as PgBouncer, RDS Proxy, or an equivalent deployment-appropriate pooler when concurrency warrants it.

Define:

- per-process connection limits;
- pool limits;
- transaction/statement timeouts;
- idle connection behaviour;
- observability for pool saturation.

### 44.6 Caching

Cache where it safely removes repeat work, including:

- expensive public feed fragments;
- entity pages;
- trending aggregates;
- show metadata;
- selected episode metadata;
- rate-limit counters;
- safe playback-selection metadata.

Never use cache as the only source of truth for entitlement, billing, ownership, or durable playback progress.

Cache invalidation MUST be explicit and observable for correctness-sensitive data.

### 44.7 CDN and origin offload

Media and cacheable static/public content SHOULD be served through an edge/CDN layer.

The application origin should not receive routine byte-range traffic for public audio/video if the CDN/media provider can serve it directly.

Track cache hit ratio, origin fetches, media-delivery errors, and origin egress so regressions are visible.

### 44.8 Capacity testing

Before materially increasing scale, test realistic workload mixes rather than isolated endpoints.

Capacity exercises SHOULD consider:

- concurrent listeners;
- bursty matchday traffic;
- creator upload spikes;
- simultaneous media processing;
- notification fan-out;
- search traffic;
- analytics ingestion;
- cache miss storms;
- degraded provider scenarios.

Document the first known bottleneck and the next scaling action rather than over-engineering every subsystem in advance.

## 45. CONCURRENCY AND TRANSACTION SAFETY

Pay special attention to:

- queue reorder;
- playback progress;
- subscription updates;
- creator team invitations;
- ownership transfers;
- download policy evaluation;
- inbox bulk actions;
- live room state;
- clip creation;
- follower counters.

Use:

- database constraints;
- unique constraints;
- transactions;
- optimistic locking;
- selective row locks when appropriate.

Do not rely solely on "check then create" application logic.

---

## 46. OBSERVABILITY

### 46.1 Structured logging

Logs should include contextual fields such as:

- request ID;
- trace/correlation ID;
- user ID where safe;
- resource ID;
- media asset ID;
- job ID;
- event ID;
- provider;
- queue/worker pool;
- operation;
- duration;
- retry count;
- status.

Do not log secrets, signed URLs, provider credentials, full tokens, or unnecessarily sensitive payloads.

### 46.2 Metrics

Track at minimum:

#### Application

- request rate;
- API latency p50/p95/p99;
- error rate;
- saturation/concurrency;
- authentication/authorisation failures where useful.

#### Database/cache

- connection pool utilisation;
- active/waiting DB connections;
- slow queries;
- lock waits/deadlocks;
- replica lag where replicas exist;
- cache hit ratio;
- cache memory pressure/evictions.

#### Queues/workers

- queue depth;
- oldest message age;
- backlog per worker;
- job latency;
- job runtime;
- retry rate;
- dead-letter count;
- worker utilisation;
- job failure rate.

#### Media

- upload success/failure;
- upload completion time;
- incomplete/abandoned uploads;
- transcoding/processing duration;
- media processing failure rate;
- provider callback failure;
- CDN cache hit ratio;
- origin fetch/egress volume;
- media delivery errors;
- signed playback token failures;
- storage growth by asset class;
- temporary-object cleanup failures.

#### Product-adjacent processing

- transcript duration/failures;
- embedding/indexing duration/failures;
- feed refresh failures;
- notification success/failure;
- playback sync conflicts;
- live-room failures.

### 46.3 Tracing

Distributed tracing is recommended where workflows cross multiple deployables/providers.

At minimum, preserve correlation IDs through:

```text
HTTP request
  → domain transaction
  → outbox/event
  → queue
  → worker
  → external provider
  → callback/webhook
```

### 46.4 Product telemetry

Technical telemetry and product analytics must remain conceptually distinct.

Operational monitoring MUST NOT require querying the high-volume product analytics warehouse for basic health questions.

### 46.5 Alerts and runbooks

Define alerts for symptoms that require action, not merely every metric excursion.

At minimum consider:

- sustained API error/latency increase;
- database saturation;
- queue backlog age breach;
- dead-letter growth;
- media-processing failure spike;
- storage/temporary-disk exhaustion;
- provider outage/error increase;
- CDN/origin anomaly;
- failed backup;
- replication lag;
- certificate/secret expiry where applicable.

Every high-severity production alert SHOULD link to an operator runbook describing diagnosis, mitigation, rollback/failover, and escalation.

## 47. TESTING STRATEGY

Every major feature must include tests across:

- happy path;
- validation failure;
- authorisation failure;
- entitlement failure;
- duplicate/retry;
- concurrency;
- migration;
- API compatibility;
- background job retry;
- malformed external provider response.

### 47.1 Unit tests

Use for:

- rule evaluators;
- access decisions;
- ranking helpers;
- state transitions;
- parsing;
- media selection;
- notification preference resolution.

### 47.2 Integration tests

Use for:

- database constraints;
- RSS fetch pipeline;
- OPML import;
- queue operations;
- playback sync;
- subscription webhook;
- media processing state;
- semantic search entitlement filtering;
- live-to-episode conversion.

### 47.3 Contract tests

Use for infrastructure/provider adapters:

- payment provider;
- storage;
- sports data;
- AI/embedding provider;
- push provider;
- media/transcoding service.

### 47.4 End-to-end tests

Critical journeys:

1. follow show → new episode → inbox → queue → play → progress;
2. play on device A → handoff → continue on device B;
3. premium preview → subscribe → ad-free media access;
4. creator uploads video → processing → transcript → publish;
5. transcript → entity extraction → entity feed;
6. create clip → render → share → deep link to episode;
7. schedule live → go live → record → publish as episode;
8. OPML import → external feed episodes appear;
9. smart playlist → smart download rule;
10. notification triggered from followed football entity.

### 47.5 Migration tests

Every destructive schema change needs migration tests with representative old data.

---

## 48. FRONTEND REQUIREMENTS

The backend must not force clients to reconstruct business rules.

Expose clear API state such as:

- accessible;
- locked;
- preview;
- available media variants;
- selected media;
- next action;
- processing state.

### 48.1 Player state

The frontend should separate:

- server canonical progress;
- local optimistic progress;
- active playback state;
- sync status.

### 48.2 Accessibility

All major interactions must support:

- keyboard on web;
- focus visibility;
- semantic controls;
- screen-reader labels;
- reduced-motion preference where applicable;
- caption/transcript alternatives.

### 48.3 Resilience

Offline-capable clients should degrade gracefully when:

- progress sync fails;
- feed refresh fails;
- analytics send fails;
- image CDN fails;
- semantic search is unavailable.

Core playback should remain usable when optional AI features fail.

---

## 49. FEATURE FLAGS AND ROLLOUT

Major features SHOULD be feature-flagged.

Examples:

- smart playlists;
- semantic search;
- video;
- clips;
- live rooms;
- matchday;
- AI creator tools.

Support:

- internal-only;
- percentage rollout;
- cohort;
- plan;
- creator opt-in.

Do not create feature flags that permanently replace proper configuration or entitlements.

Remove stale flags after rollout.

---

## 50. DATA MIGRATION DISCIPLINE

For every schema evolution:

1. add new structures compatibly;
2. backfill safely;
3. dual-read/dual-write only when strictly necessary and temporary;
4. migrate callers;
5. validate parity;
6. remove obsolete writes;
7. remove obsolete reads;
8. delete superseded schema/code;
9. document completion.

Avoid long-term dual systems.

Large backfills MUST:

- be chunked;
- resumable;
- observable;
- rate-limited;
- safe under concurrent writes.

---

## 51. DELETION DISCIPLINE

The repository must not retain "just in case" superseded implementations indefinitely.

Before deleting:

- identify callers;
- migrate callers;
- add tests;
- validate data migration;
- confirm compatibility window.

Then delete:

- dead models;
- obsolete services;
- duplicate settings;
- old endpoints;
- unused feature flags;
- obsolete background tasks;
- dead migrations only when repository policy safely permits squashing rather than rewriting production migration history.

---

## 52. DOCUMENTATION REQUIREMENTS

Every substantial feature must document:

- purpose;
- domain owner;
- data model;
- API;
- permissions;
- background jobs;
- events;
- failure modes;
- operational concerns;
- observability;
- tests.

### 52.1 Required repository documents

Maintain or create:

```text
docs/
    architecture/
    features/
    operations/
    security/
    adr/
```

Recommended files:

```text
docs/architecture/domain-map.md
docs/architecture/event-catalog.md
docs/architecture/media-pipeline.md
docs/architecture/playback-sync.md
docs/architecture/analytics.md
docs/security/rss-fetching.md
docs/security/media-access.md
docs/operations/background-jobs.md
docs/operations/media-processing.md
docs/features/semantic-search.md
docs/features/live-podcasting.md
```

The infrastructure/media work SHOULD also maintain or create, as appropriate:

```text
docs/architecture/media-platform.md
docs/architecture/production-infrastructure.md
docs/operations/media-runbook.md
docs/operations/disaster-recovery.md
docs/operations/backup-restore.md
docs/operations/cost-capacity.md
```

Do not create duplicate documentation if equivalent canonical files already exist; extend the canonical documents instead.

### 52.2 ADRs

Use ADRs for meaningful trade-offs such as:

- vector-search infrastructure;
- live media infrastructure;
- analytics store;
- video streaming format;
- generic follow model;
- event bus;
- remote-device protocol.

Do not create ADRs for trivial implementation details.

---

## 53. IMPLEMENTATION STATUS DOCUMENT

Maintain:

```text
SANFOOTBALL_IMPLEMENTATION_STATUS.md
```

It MUST include:

- current phase;
- completed tasks;
- in-progress tasks;
- blocked items;
- migrations performed;
- legacy code removed;
- test status;
- known risks;
- ADRs created;
- deployment notes.

Update it continuously during implementation.

Do not wait until the end.

---

## 54. PHASED IMPLEMENTATION PLAN

The coding agent MUST execute feature work sequentially unless repository conditions justify a documented dependency change.

---

## PHASE 0 — BASELINE, INVENTORY, AND SAFETY GATE

Before implementing any new feature:

1. read this file in full;
2. read Part I — Core Refactor, Canonicalisation, and Modernisation of this file in full;
3. inspect repository structure;
4. inspect git status;
5. inspect documentation;
6. inspect current test suite;
7. run baseline checks;
8. map canonical domains;
9. map public APIs;
10. map models;
11. map migrations;
12. map background tasks;
13. map events/signals;
14. map media storage;
15. map authentication;
16. map subscription/entitlement logic;
17. map queue/progress/download logic;
18. map search/recommendations;
19. map community logic;
20. map football entity logic;
21. map deployment topology;
22. map object/media storage providers and local filesystem dependencies;
23. map CDN/edge behaviour;
24. map direct upload/download flows;
25. map database/cache/broker hosting and connection limits;
26. map worker pools and resource isolation;
27. map backups/restore/DR;
28. map observability/alerts;
29. map infrastructure-as-code and deployment pipeline;
30. map current storage, bandwidth, compute, and provider cost drivers.

Produce/update:

```text
SANFOOTBALL_IMPLEMENTATION_STATUS.md
```

with the baseline.

#### Phase 0 Gate

Do not proceed if:

- the prior refactor is materially incomplete in an area the next feature depends on;
- canonical ownership cannot be identified;
- baseline tests are unknown;
- a new feature would necessarily duplicate unresolved legacy systems.

If a required Part I canonicalisation is incomplete, finish that canonicalisation under Part I of this file, document it in `SANFOOTBALL_IMPLEMENTATION_STATUS.md`, satisfy the relevant phase gate, then return to this feature programme.

---

## PHASE 0A — PRODUCTION INFRASTRUCTURE FOUNDATION

This phase establishes architecture boundaries; it does NOT require deploying every large-scale service immediately.

Inspect and define:

- current hosting model;
- object/media storage abstraction;
- current `FileField`/filesystem usage;
- direct-upload capability;
- CDN/media delivery path;
- video provider abstraction;
- container/process boundaries;
- web/worker resource isolation;
- database backup and connection strategy;
- Redis/cache/broker deployment;
- secrets management;
- telemetry;
- IaC/CI/CD status;
- current storage and bandwidth cost visibility.

Implement the minimum production-safe foundation:

- canonical `MediaAsset`/provider-location abstraction if missing;
- direct upload-intent service;
- object-storage adapter;
- video-platform adapter boundary;
- stateless web assumptions;
- separate web/worker commands;
- media lifecycle cleanup;
- required infrastructure configuration validation;
- baseline infrastructure documentation and ADRs;
- baseline observability for uploads/media jobs/provider errors.

Gate:

- no production dependency on durable local media files;
- application can run multiple web instances without shared local disk;
- media bytes need not traverse Django for normal creator upload/playback;
- provider choice is not embedded in canonical domain logic;
- backup/restore and secret strategy are documented;
- infrastructure decisions are represented in IaC or explicitly tracked for migration.

---

## PHASE 1 — ADVANCED PLAYER FOUNDATION

Implement:

- canonical player preferences;
- playback speed;
- per-show override;
- skip durations;
- sleep timer;
- silence trim support where client architecture permits;
- voice/loudness enhancement hooks;
- playback markers;
- creator-defined intro/outro;
- automated marker pipeline if technically ready.

Tests:

- preference resolution;
- progress;
- entitlement;
- marker bounds;
- playback-rate analytics.

Gate:

- no duplicate progress state;
- no new player-specific entitlement logic;
- backward compatibility preserved.

---

## PHASE 2 — SMART LIBRARY AND SMART DOWNLOADS

Implement:

- playlist type;
- smart rule engine;
- episode inbox;
- archive/dismiss state;
- download policies;
- storage policy metadata;
- data-saver preference integration.

Tests:

- rule validation;
- query bounds;
- deduplication;
- bulk actions;
- pinned download protection.

Gate:

- canonical queue remains the only queue;
- canonical download state remains the only download state.

---

## PHASE 3 — CROSS-DEVICE PLAYBACK

Implement:

- device records;
- active playback session;
- optimistic concurrency;
- heartbeat/update protocol;
- transfer/handoff;
- conflict resolution;
- device revocation where appropriate.

Load-test progress updates.

Gate:

- stale devices cannot corrupt current progress;
- queue is preserved;
- entitlement rechecked.

---

## PHASE 4 — RSS/OPML PORTABILITY

Implement:

- external feed subscription;
- controlled RSS fetcher;
- SSRF protections;
- refresh scheduling;
- OPML import;
- OPML export;
- import progress;
- deduplication.

Gate:

- security review;
- malformed feed tests;
- large import tests;
- private URL/token review.

---

## PHASE 5 — SHARING: CLIPS AND QUOTE CARDS

Implement:

- canonical clip;
- permission rules;
- rendering jobs;
- transcript captions;
- quote cards;
- deep links;
- public/unlisted/private visibility;
- moderation/reporting hooks.

Gate:

- premium leakage tests;
- external-feed policy tests;
- rendering retry tests.

---

## PHASE 6 — VIDEO PODCASTS

Implement:

- media variant extension;
- video ingestion;
- transcoding;
- adaptive delivery strategy;
- audio extraction;
- audio/video switching;
- thumbnails;
- quality selection;
- data-saver integration.

Gate:

- direct/resumable large-file upload;
- no full-file Django proxy path for routine ingestion;
- object-storage/video-provider abstraction;
- adaptive delivery strategy;
- storage/CDN lifecycle review;
- signed/private entitlement delivery;
- playback sync;
- failure recovery and provider callback idempotency;
- queue/resource isolation;
- storage and delivery cost observability.

---

## PHASE 7 — FOOTBALL INTELLIGENCE

Implement:

- entity aliases;
- transcript entity extraction;
- mention provenance/confidence;
- human correction;
- entity episode pages;
- timestamped mentions;
- followable football entities.

Gate:

- ambiguous-entity tests;
- reprocessing preserves corrections;
- no duplicate football entity database.

---

## PHASE 8 — SEMANTIC SEARCH

Implement:

- transcript chunking;
- embedding provider abstraction;
- vector index;
- metadata filters;
- entitlement-aware retrieval;
- source/timestamp results;
- optional grounded synthesis.

Gate:

- premium leakage test;
- hallucination/source tests;
- provider outage fallback;
- cost/usage controls.

---

## PHASE 9 — INTELLIGENT NOTIFICATIONS AND PERSONALISED HOME

Implement:

- follow-driven notification rules;
- preference resolution;
- deduplicated fan-out;
- entity notifications;
- home feed composition;
- matchday/followed-entity modules.

Gate:

- notification duplication tests;
- feed performance;
- privacy review.

---

## PHASE 10 — CREATOR ANALYTICS

Implement:

- analytics event contract;
- ingestion;
- aggregates;
- retention;
- replay hotspots;
- drop-off signals;
- creator dashboard APIs;
- conversion analytics.

Gate:

- analytics event volume test;
- aggregation correctness;
- privacy thresholds;
- query performance.

---

## PHASE 11 — NETWORKS, TEAMS, AND ADVANCED COMMERCIAL PACKAGING

Implement:

- networks/channels;
- network show membership;
- creator teams;
- capability-based permissions;
- network subscriptions;
- ad-free media variants;
- aggregate creator analytics.

Gate:

- ownership transfer test;
- permission matrix test;
- entitlement bundle test;
- audit logs.

---

## PHASE 12 — LIVE PODCASTING

Implement:

- broadcast lifecycle;
- scheduling;
- room permissions;
- participant roles;
- moderation;
- recording;
- processing;
- conversion to normal episode.

Gate:

- failure recovery;
- recording durability;
- entitlement;
- moderation;
- capacity testing.

---

## PHASE 13 — MATCHDAY EXPERIENCE

Implement:

- fixture-linked rooms;
- pre/live/post phases;
- match-aware chapters;
- event/entity alignment;
- match content collections;
- "Listen Around the Match";
- player ratings/polls where existing community primitives support them.

Gate:

- external sports-data failure tolerance;
- fixture identity consistency;
- collection/queue reuse.

---

## PHASE 14 — LISTENER ENGAGEMENT LAYER

Implement:

- listening statistics;
- annual recap;
- tasteful achievements;
- shareable recap assets.

Gate:

- privacy;
- aggregation correctness;
- deterministic achievement rules.

---

## PHASE 15 — CONNECTED DEVICES

Implement according to client priority:

- casting;
- automotive;
- TV;
- speaker integration;
- wearables.

Gate:

- canonical playback session reuse;
- device security;
- entitlement;
- remote command authentication.

---

## PHASE 16 — TRANSCRIPT TRANSLATION AND CREATOR AI

Implement:

- transcript translation;
- version linkage;
- creator metadata drafting;
- title/description suggestions;
- chapter suggestions;
- clip candidates;
- entity suggestions;
- social copy drafts.

Gate:

- creator approval;
- provenance;
- privacy;
- cost controls;
- provider abstraction.

---

## 55. ACCEPTANCE SCENARIOS

The following scenarios MUST eventually work end-to-end.

### Scenario A — Premium football listener

1. User follows Arsenal.
2. A new Arsenal-related episode is published.
3. It appears in Inbox.
4. User adds it to queue.
5. Smart download obtains data-saver audio on mobile preference.
6. User plays at 1.7x.
7. Intro is skipped according to user preference.
8. Progress syncs.
9. User changes device.
10. Playback resumes at correct position.
11. User selects a transcript quote.
12. Quote card deep-links to correct moment.

### Scenario B — Premium conversion

1. User opens a premium episode.
2. Access policy permits a preview.
3. User listens to preview.
4. Subscription offer is shown.
5. User subscribes.
6. Webhook is processed idempotently.
7. Entitlement becomes active.
8. Player selects ad-free media variant.
9. Conversion analytics attribute within defined rules.

### Scenario C — Creator video workflow

1. Creator uploads video.
2. Upload validates.
3. Video transcodes.
4. Audio derivative is produced.
5. Transcript is generated.
6. Chapters are generated.
7. entities are extracted.
8. Creator reviews AI suggestions.
9. Episode is published.
10. Listeners can switch audio/video without losing position.

### Scenario D — Football semantic discovery

1. Listener searches:
   "What did they say about Saka against Liverpool?"
2. Search retrieves entitled transcript segments.
3. Results show episodes and timestamps.
4. Optional synthesis cites those moments in the UI.
5. User taps a result.
6. Player seeks to correct timestamp.

### Scenario E — Live-to-podcast

1. Creator schedules Arsenal post-match live.
2. Followed users receive one deduplicated notification.
3. Broadcast goes live.
4. Members join.
5. Comments/polls operate through canonical community primitives.
6. Recording completes.
7. Broadcast transitions to processing.
8. Episode is created.
9. Transcript/chapters/entities process.
10. Creator publishes highlights.

### Scenario F — Match collection

1. Fixture exists.
2. Preview episode links to fixture.
3. Live room links to fixture.
4. Post-match episode links to fixture.
5. Tactical episode links to fixture.
6. "Listen Around the Match" presents ordered collection.
7. User plays collection through canonical queue.

### Scenario G — External podcast migration

1. User imports OPML.
2. Import validates feeds.
3. Malformed feeds are reported without aborting valid imports.
4. Duplicates collapse.
5. External episodes appear in library.
6. Premium/private SanFootball logic is not incorrectly applied.
7. User can export subscriptions.

---

## 56. ANTI-PATTERNS — STRICTLY FORBIDDEN

Do NOT:

- create `smart_queue` as a second queue implementation;
- create `video_episode` as a separate episode hierarchy;
- create an `ai_search` app that owns another transcript store;
- create per-feature subscription checks;
- hard-code plan names across views;
- use client flags as authorisation;
- expose permanent premium storage URLs;
- synchronously transcode media in request handlers;
- synchronously generate AI output in critical publish transactions;
- perform unbounded transcript/vector searches;
- load full media files into application memory;
- use unrestricted user-authored SQL-like smart playlist expressions;
- build RSS ingestion without SSRF protection;
- use framework signals as an invisible workflow engine;
- keep two progress systems during normal operation indefinitely;
- silently swallow background job failures;
- reprocess AI/entity data without preserving human corrections;
- publish generated AI metadata without creator approval;
- reveal premium transcript text through semantic search;
- treat external RSS content as if SanFootball owns derivative rights;
- put provider-specific sports payloads in core domain models;
- send notification fan-out inside a database transaction;
- calculate full creator analytics from raw events on every dashboard request;
- create separate community primitives for matchday when comments/polls/reactions can be reused;
- create separate queues for match collections;
- build device playback state that ignores canonical progress;
- introduce microservices simply because a feature is "large";
- leave placeholder/TODO production code presented as completed implementation;
- disable tests to make CI pass;
- rewrite production migration history casually;
- remove public APIs before callers are migrated;
- leave dead duplicate code after migration is complete.

---

## 57. CODE QUALITY REQUIREMENTS

The agent MUST follow repository formatting, linting, typing, and testing standards.

Where not already defined, establish:

- consistent formatter;
- linter;
- type checking appropriate to project;
- import sorting if separate;
- pre-commit hooks where useful;
- CI enforcement.

Code must favour:

- explicit names;
- small cohesive services;
- testable pure logic;
- dependency injection/adapters at infrastructure boundaries;
- typed contracts where practical;
- immutable value objects where appropriate;
- documented public interfaces.

Avoid:

- giant service classes;
- circular imports;
- hidden global state;
- magic strings;
- duplicated constants;
- unnecessary inheritance;
- generic "utils.py" dumping grounds.

---

## 58. CONFIGURATION

All new features and infrastructure integrations MUST use canonical, typed/validated configuration.

Configuration must support:

- environment variables and secret-manager injection;
- safe development defaults where appropriate;
- explicit production requirements;
- environment-specific overrides;
- validation at startup;
- clear failure for missing mandatory production settings;
- provider selection through canonical settings rather than scattered conditionals.

Examples:

```text
CLIP_MAX_DURATION
RSS_FETCH_TIMEOUT
RSS_MAX_RESPONSE_BYTES
MEDIA_UPLOAD_MAX_BYTES
MEDIA_UPLOAD_MAX_DURATION
MEDIA_STORAGE_PROVIDER
MEDIA_DELIVERY_PROVIDER
VIDEO_PLATFORM_PROVIDER
MEDIA_PUBLIC_BASE_URL
MEDIA_PRIVATE_URL_TTL
MEDIA_TEMP_RETENTION_HOURS
MEDIA_ORIGINAL_RETENTION_POLICY
MEDIA_MULTIPART_THRESHOLD_BYTES
MEDIA_PROCESSING_CONCURRENCY
SEMANTIC_SEARCH_TOP_K_MAX
AI_PROVIDER
EMBEDDING_PROVIDER
LIVE_PROVIDER
NOTIFICATION_PROVIDER
DATABASE_POOL_MODE
DATABASE_MAX_CONNECTIONS
CACHE_PROVIDER
QUEUE_PROVIDER
OTEL_EXPORTER_*
```

Do not read environment variables ad hoc throughout the codebase.

Production configuration MUST distinguish:

- secret values;
- deploy-time infrastructure values;
- feature flags;
- product policy;
- runtime-tunable operational settings.

Do not make a redeploy necessary for every product-policy adjustment if a safe canonical runtime configuration mechanism already exists.

## 59. DEPENDENCY MANAGEMENT

Before adding a dependency:

1. determine whether the repository already has a suitable dependency;
2. assess maintenance;
3. assess security;
4. assess licence;
5. assess bundle/runtime cost;
6. document material infrastructure dependencies.

Do not add a major package for a trivial helper.

Pin versions according to repository policy.

### 59.1 Mandatory `pycflare` Git dependency

SANFootball MUST install `pycflare` from its GitHub repository rather than assume a PyPI release is available or current.

The dependency declaration MUST use a PEP 508 direct-VCS reference with the required extras. The baseline dependency at the time of this amendment is:

```text
pycflare[storages,media] @ git+https://github.com/Leydotpy/pycflare.git@f214c80de3843d47f0593386a60169c77e8bc801
```

Equivalent `uv`/lockfile syntax is acceptable, but these requirements are mandatory:

1. install from `https://github.com/Leydotpy/pycflare`;
2. include the `storages` and `media` extras for Django/R2 + Images/Stream support;
3. pin an immutable tag or commit in production/CI rather than tracking an unpinned moving branch;
4. commit the resolved lockfile according to repository policy;
5. update the pin only through an explicit dependency upgrade with tests for upload, private delivery, webhook verification, and Django storage compatibility;
6. do not vendor/fork a private copy into SANFootball merely for convenience;
7. if SANFootball needs a Cloudflare capability that `pycflare` does not expose, first determine whether the package should be extended. A temporary raw-provider escape hatch requires an ADR, tests, strict isolation inside the Cloudflare adapter, and a plan to remove it.

The package is an **infrastructure integration dependency**, not a domain dependency. Core models/services MUST NOT import `pycflare`.

---

## 60. EXTERNAL PROVIDER ADAPTERS

Infrastructure integrations MUST use explicit adapters/interfaces.

Potential provider categories:

- object storage;
- media delivery/CDN;
- video platform/transcoding;
- email;
- push;
- payments;
- sports data;
- embeddings;
- language models;
- vector database;
- live media;
- analytics warehouse;
- secrets;
- observability exporters.

Core domain/application services should depend on interfaces, not vendor SDKs where practical.

### 60.1 Required media interfaces

The media subsystem SHOULD expose canonical interfaces conceptually equivalent to:

```text
ObjectStorage
    create_upload_intent(...)
    complete_upload(...)
    head(...)
    open_or_sign_download(...)
    delete(...)
    copy_or_promote(...)
    set_retention_or_class(...)

ImagePlatform
    create_upload_intent(...)
    get_status(...)
    build_public_variant(...)
    sign_private_variant(...)
    delete(...)

VideoPlatform
    create_upload_intent(...)
    get_status(...)
    get_playback_descriptor(...)
    sign_playback(...)
    delete(...)

MediaProcessor
    probe(...)
    transcode(...)
    extract_audio(...)
    render_thumbnail(...)
    render_waveform(...)

MediaDelivery
    resolve_public_delivery(...)
    resolve_private_delivery(...)

MediaAccessController
    authorise_playback(...)
    authorise_download(...)
```

The exact class/function names MUST follow existing repository conventions; the architectural boundary is mandatory, not these literal names.

For the current Cloudflare implementation, map those interfaces through a narrow infrastructure package conceptually equivalent to:

```text
ObjectStorage adapter
    -> pycflare.storage.R2Client / AsyncR2Client
    -> pycflare Django R2 storage backend where Django FileField/Storage integration is appropriate

ImagePlatform adapter
    -> pycflare.media.ImagesClient / AsyncImagesClient
    -> ImagesURLBuilder / ImagesURLSigner for controlled delivery

VideoPlatform adapter
    -> pycflare.media.StreamClient / AsyncStreamClient
    -> StreamURLBuilder / StreamTokenSigner for controlled playback
    -> StreamWebhookVerifier for processing callbacks
```

Do not expose these classes as the application/domain interfaces themselves.

### 60.2 Reference deployment profile

Unless an ADR or deployment constraint selects otherwise, the preferred production reference profile is:

```text
Edge / DNS / WAF / CDN        → Cloudflare
Python Cloudflare integration → pycflare (Git-pinned)
Object/audio storage          → Cloudflare R2 via pycflare
Managed images                → Cloudflare Images via pycflare
Managed video                 → Cloudflare Stream via pycflare
Application containers        → AWS ECS/Fargate or equivalent
PostgreSQL                    → Managed PostgreSQL / Amazon RDS
DB connection pooling         → RDS Proxy / PgBouncer / equivalent
Cache                         → Managed Redis/Valkey
Queues                        → Existing canonical broker/task layer; managed queue where selected
Container registry            → ECR/GHCR or equivalent
Infrastructure as Code        → Terraform or Pulumi
Telemetry                     → OpenTelemetry + chosen metrics/logs/traces backend
```

This is a deployment default, not domain architecture. Replacing a vendor MUST NOT require rewriting episodes, subscriptions, entitlements, playback, or media business logic.

### 60.3 Provider capability records

Where provider capabilities differ, model capability discovery/configuration explicitly rather than scattering `if provider == ...` branches.

Examples:

- supports multipart/resumable upload;
- supports signed playback;
- supports adaptive video;
- supports lifecycle/storage classes;
- supports webhooks;
- supports origin pull;
- supports private downloads;
- supports server-side copy.

### 60.4 Provider failure

External providers are fallible.

Each adapter MUST define:

- timeout;
- retry policy;
- rate-limit behaviour;
- idempotency behaviour;
- error mapping;
- health/observability fields;
- circuit-breaker/degradation behaviour where useful;
- migration/export path for durable data where applicable.

## 61. FAILURE PHILOSOPHY

Optional enhancement failures must not destroy core content.

Examples:

- transcript failure does not delete episode;
- entity extraction failure does not prevent playback;
- semantic indexing failure does not prevent lexical search;
- quote-card rendering failure does not corrupt transcript;
- annual recap failure does not affect analytics;
- notification failure does not roll back episode publication.

Represent partial processing state explicitly.

---

## 62. ADMIN AND OPERATOR TOOLING

Where operationally useful, provide admin tooling for:

- failed media jobs;
- failed feed refresh;
- invalid RSS feeds;
- OPML imports;
- transcript regeneration;
- entity correction;
- clip moderation;
- live broadcast recovery;
- notification failures;
- provider status;
- subscription webhook replay;
- analytics backfill.

Admin actions must be authorised and audited.

---

## 63. MODERATION AND COMMUNITY SAFETY

Community and live features require:

- report;
- hide/delete;
- mute;
- block where product supports it;
- moderator roles;
- rate limits;
- anti-spam;
- audit log;
- appeal/review workflow where appropriate.

Timestamp comments and live comments should reuse canonical moderation concepts.

---

## 64. CONTENT AND MEDIA LIFECYCLE

Define consistent lifecycle states for content.

Example content lifecycle:

```text
DRAFT
PROCESSING
READY
SCHEDULED
PUBLISHED
UNLISTED
ARCHIVED
FAILED
```

Exact states should align with the existing repository.

Media processing state and publication state MUST remain separate when they have different semantics.

Do not encode complex lifecycle only through nullable timestamps.

### 64.1 Media object lifecycle

Every stored object/asset category MUST have an explicit lifecycle policy.

At minimum distinguish:

```text
creator/source originals
published audio derivatives
published video/provider assets
artwork/thumbnails
waveforms
transcripts/captions
clips/previews
temporary processing files
incomplete uploads
failed-processing artefacts
backups/archives
```

For each category document:

- storage location/provider;
- visibility;
- retention duration;
- storage class/tier where supported;
- deletion trigger;
- whether it is regenerable;
- whether legal/billing retention overrides deletion;
- whether creator deletion must cascade;
- backup/replication requirement.

Temporary processing files and incomplete multipart/resumable uploads MUST be garbage-collected automatically.

### 64.2 Deletion safety

Deletion SHOULD use a staged process where accidental loss would be severe:

```text
application marks asset pending deletion
    ↓
revalidation / grace period where policy requires
    ↓
provider deletion
    ↓
verification / tombstone / audit
```

Do not orphan provider objects indefinitely after canonical records are deleted.

## 65. DEEP LINKS

All major content types should have stable deep links:

- show;
- episode;
- episode timestamp;
- chapter;
- clip;
- quote;
- club;
- player;
- competition;
- fixture;
- live room;
- network.

Deep-link resolution must:

- respect entitlement;
- support web fallback;
- support mobile app association later.

---

## 66. MEDIA TIMELINE CONSISTENCY

A critical cross-feature rule:

All of the following must refer to the same canonical media timeline:

- transcript segments;
- chapters;
- bookmarks;
- clip start/end;
- entity mentions;
- analytics retention;
- playback progress;
- match-aware markers.

Playback speed, silence trimming, or client effects MUST NOT mutate the canonical timeline.

---

## 67. DATA RETENTION, AGGREGATION, AND STORAGE GROWTH

High-volume analytics, playback heartbeat data, media assets, logs, and temporary processing artefacts cannot grow forever without policy.

Define:

- raw event retention;
- aggregation cadence;
- archival;
- deletion/anonymisation;
- partitioning strategy if required;
- media lifecycle policy;
- log retention;
- backup retention;
- transcript/vector re-index retention;
- temporary-object cleanup;
- cost attribution/tagging.

Do not delete data required for billing/audit/legal obligations contrary to law or product policy.

### 67.1 Storage accounting

Track storage by meaningful dimensions such as:

- tenant/creator/network where applicable;
- source vs derivative;
- audio vs video vs image vs transcript;
- hot/standard vs infrequent/archive class;
- temporary vs durable;
- provider;
- age cohort.

This data SHOULD support capacity planning, creator quotas, abuse detection, and cost allocation.

### 67.2 Quotas and guardrails

The application SHOULD be capable of enforcing configurable:

- per-upload size limits;
- duration limits;
- creator/network storage allowances;
- daily/monthly upload limits;
- concurrent processing limits;
- video usage limits where commercially necessary.

Quota enforcement MUST be based on canonical policy/entitlement rather than hard-coded plan names.

## 68. REPOSITORY-WIDE FIRST ACTION PROTOCOL FOR EVERY AGENT

Before writing code, the implementation agent MUST:

1. read `AGENTS.md` fully;
2. locate and read any parent/child `AGENTS.md`;
3. read Part I — Core Refactor, Canonicalisation, and Modernisation of this file;
4. read `SANFOOTBALL_IMPLEMENTATION_STATUS.md`;
5. inspect repository status;
6. identify current branch;
7. identify modified/untracked files;
8. do not overwrite user changes;
9. inspect architecture docs;
10. inspect tests;
11. identify domain owner for requested feature;
12. identify public and internal callers;
13. identify relevant models/migrations;
14. identify relevant permissions;
15. identify background tasks/events;
16. identify existing abstractions that can be extended;
17. inspect hosting/storage/CDN/queue/database/provider impact for the requested feature;
18. inspect cost, lifecycle, backup, and observability implications;
19. write/update implementation status;
20. only then begin changes.

If work spans multiple phases, execute one reviewable phase at a time.

---

## 69. REQUIRED WORKING STYLE FOR CODING AGENTS

Agents MUST implement, not merely describe.

For each task:

1. inspect;
2. design;
3. implement;
4. migrate;
5. test;
6. document;
7. remove superseded code;
8. report exact result.

Do not stop at:

```text
"Here is how you could implement it."
```

when the user has requested implementation.

Do not create fake placeholders and call the feature complete.

---

## 70. DEFINITION OF DONE

A feature is NOT done merely because a model or endpoint exists.

A feature is done when:

- architecture fits canonical domain;
- data model is migrated;
- old callers are migrated;
- security is enforced;
- permissions are correct;
- retries are safe;
- failure states are represented;
- API is documented;
- UI contract is usable;
- tests pass;
- observability exists;
- performance is acceptable;
- infrastructure impact is documented;
- storage/delivery lifecycle is defined for new media;
- provider integration remains behind canonical adapters;
- new high-volume work has capacity/backpressure behaviour;
- cost/usage telemetry exists where the feature can materially increase spend;
- docs are updated;
- status file is updated;
- dead superseded code is removed;
- no known high-severity regression remains.

---

## 71. REVIEW CHECKLIST

Before merging each feature, reviewers/agents should answer:

### Architecture

- Does this extend the canonical domain?
- Did it accidentally create duplicate state?
- Is ownership clear?
- Are boundaries explicit?

### Security

- Is server-side authorisation enforced?
- Could premium content leak?
- Is untrusted input validated?
- Are external requests protected?

### Data

- Are constraints correct?
- Is migration safe?
- Is concurrency handled?
- Are indexes justified?

### Performance

- Are queries bounded?
- Any N+1?
- Heavy work async?
- Large files streamed?
- Caching safe?

### Reliability

- Idempotent?
- Retryable?
- Failure observable?
- Partial failure safe?
- Backpressure defined?
- DLQ/failed-job path operable where relevant?

### Infrastructure

- Does this require durable local disk? It must not in production.
- Can web and worker workloads scale independently?
- Does large media bypass Django byte transport?
- Is provider-specific code isolated?
- Are lifecycle/retention rules defined?
- Are backups/restore affected?
- Are secrets/permissions least-privilege?
- Is cost/storage growth observable?
- Does the deployment/IaC need updating?

### Product

- Does it improve listener/creator value?
- Does it preserve football-first direction?
- Is it consistent with existing UX concepts?

### Testing

- Happy path?
- Failure path?
- Permission?
- Entitlement?
- Duplicate/retry?
- Concurrency?
- Migration?

### Documentation

- Feature docs?
- API docs?
- ADR where required?
- Status updated?

---

## 72. LONG-TERM ARCHITECTURAL DIRECTION

SanFootball should remain capable of evolving toward:

```text
Content Platform
      +
Listening Platform
      +
Football Knowledge Graph
      +
Creator Platform
      +
Community Platform
      +
Commercial Platform
      +
Live Audio Platform
      +
Media Platform
```

without becoming a collection of disconnected applications.

The deployment architecture MUST distinguish the **control plane** from the **media plane**.

```text
                              INTERNET
                                 │
                                 ▼
                     ┌─────────────────────┐
                     │ Edge / DNS / WAF    │
                     │ CDN / Rate limits   │
                     └──────────┬──────────┘
                                │
                 ┌──────────────┴──────────────┐
                 │                             │
                 ▼                             ▼
        CONTROL PLANE                    MEDIA PLANE

   ┌────────────────────┐        ┌─────────────────────────┐
   │ Web / API / Realtime│        │ Audio / Images / Files │
   │ Django / ASGI       │        │ Object Storage + CDN    │
   └──────────┬─────────┘        └────────────┬────────────┘
              │                                │
              │                       ┌────────┴─────────┐
              │                       │ Managed Video / │
              │                       │ Adaptive Stream │
              │                       └──────────────────┘
              │
   ┌──────────┼────────────────────────────────────────────┐
   │          │                 │                          │
   ▼          ▼                 ▼                          ▼
PostgreSQL  Redis/Valkey   Domain Events/Outbox       Search/Analytics
                                 │
                                 ▼
                         Queue / Broker Layer
                                 │
                 ┌───────────────┼────────────────┐
                 ▼               ▼                ▼
              Workers       Media Workers      AI/Indexers
```

The fundamental rule is:

```text
Django decides WHO may access media.
Django does not transport routine media bytes.
```

A feature may require specialised infrastructure, but infrastructure must not dictate domain ownership.

The modular monolith remains the preferred application architecture until measured scaling, team autonomy, reliability isolation, or deployment requirements justify extracting a deployable service. Infrastructure decomposition does not automatically require domain microservices.

## 73. PRODUCTION HOSTING AND INFRASTRUCTURE MANDATE

The production platform MUST be designed so application compute, database, cache, queues, media storage, media processing, search, analytics, and edge delivery can scale independently.

The architecture MUST NOT rely on a single large VPS containing Django, PostgreSQL, Redis, media files, FFmpeg, background workers, and backups as the long-term production design.

A single-machine development environment is acceptable. Production boundaries must nevertheless preserve migration to independently managed/scaled infrastructure.

### 73.1 Production principles

1. application servers are stateless/disposable;
2. durable media lives in object storage or a managed media platform;
3. playback bytes are delivered by CDN/media infrastructure;
4. heavy work leaves the HTTP request path;
5. web and worker compute scale independently;
6. PostgreSQL is metadata/transactional truth, not blob storage;
7. Redis/Valkey is acceleration/coordination, not canonical durable truth;
8. infrastructure is reproducible through code;
9. all critical services are observable;
10. backup, restore, and disaster recovery are tested;
11. vendor dependencies are isolated behind adapters;
12. cost is a measurable non-functional requirement.

---

## 74. EDGE, DNS, WAF, AND CDN

The public platform MUST terminate through Cloudflare edge services before reaching application origin in the current production baseline, unless a later ADR explicitly replaces that provider.

The current production deployment baseline MUST use Cloudflare for:

- authoritative/proxied DNS where appropriate;
- TLS termination/management;
- DDoS mitigation;
- WAF;
- bot/rate controls where appropriate;
- CDN/caching;
- media/public asset delivery integration;
- Cloudflare Images delivery for managed image variants;
- Cloudflare Stream delivery for managed video;
- R2 custom-domain delivery for public object/audio assets.

### 74.1 Origin protection

Application origins SHOULD:

- reject direct public access where deployment permits;
- trust proxy headers only from configured trusted proxies;
- enforce HTTPS;
- validate host headers;
- use least-exposure security groups/firewalls;
- expose only required ports;
- separate internal services from the public network.

### 74.2 Cache policy

Define explicit cache policies for:

- public show/episode pages or API fragments;
- artwork;
- transcripts where public;
- immutable static assets;
- public media;
- protected media metadata.

Personalised/entitled responses MUST NOT be cached across users unless the cache key and privacy model make this provably safe.

### 74.3 CDN invalidation/versioning

Prefer immutable/versioned asset URLs over frequent cache purges.

When invalidation is necessary it MUST be observable and scoped; avoid broad global purges as routine application behaviour.

---

## 75. OBJECT STORAGE ARCHITECTURE

Object storage is the canonical home for large durable binary assets not delegated to a managed video provider.

The current implementation MUST use Cloudflare R2 through `pycflare`. SANFootball application code MUST depend on its own `ObjectStorage` abstraction; the Cloudflare adapter is the only layer that may depend on `pycflare` R2 classes.

Django `STORAGES` integration SHOULD use the `pycflare` Django R2 backend where ordinary Django storage semantics are appropriate. Large creator upload paths MUST still prefer direct browser-to-R2 transfer rather than posting the full body to Django.

Public production object/audio delivery MUST use a configured R2 custom domain/Cloudflare edge path. `r2.dev` is development-only and MUST NOT be the production media hostname.

Private R2 delivery MUST use a short-lived backend-issued capability. A presigned R2 URL is a bearer credential: do not log it, persist it in durable client state, include it in analytics, or expose it before AccessPolicy succeeds.

### 75.1 Bucket/prefix strategy

Separate security/lifecycle domains either by bucket or explicit prefixes. A conceptual layout:

```text
originals/
published/audio/
published/images/
transcripts/
waveforms/
clips/
previews/
temporary/uploads/
temporary/processing/
exports/
backups-or-replication-metadata/
```

Do not expose implementation prefixes as permanent public API semantics.

### 75.2 Object naming

Object keys SHOULD be opaque/stable and collision-resistant.

Do not use raw user-supplied filenames as trusted storage keys. Preserve the original filename only as metadata where useful.

### 75.3 Integrity

Track checksums/ETags where meaningful and verify integrity during ingest, copy/promotion, migration, or processing.

### 75.4 Lifecycle rules

Use provider lifecycle policies where supported for:

- incomplete multipart uploads;
- temporary uploads;
- processing intermediates;
- ageing originals moving to less frequently accessed classes where product policy permits;
- expired exports.

Application cleanup tasks MAY supplement provider lifecycle rules but should not replace simple provider-native expiration where safe.

### 75.5 Storage migrations

A storage migration tool/process SHOULD be capable of:

- enumerating canonical assets;
- copying assets to a new provider/location;
- verifying checksum/size;
- atomically changing canonical location metadata;
- preserving old location until validation completes;
- retrying partial failures;
- reporting progress;
- rolling back pointer changes where practical.

### 75.6 Cloudflare Images architecture

Cloudflare Images is the selected managed image service for user-facing artwork/photographs where SANFootball benefits from managed variants, transformations, direct creator upload, or signed private delivery.

Use `pycflare` to:

- create one-use Direct Creator Upload capabilities after authentication/authorization;
- attach safe ownership/canonical metadata;
- manage named variants/transforms centrally rather than scattering arbitrary size strings across clients;
- require signed URLs for images whose disclosure is gated;
- sign private image delivery server-side;
- delete/reconcile provider objects through the canonical image adapter.

Do not use custom image IDs for private Images assets when that would conflict with signed-delivery requirements. Canonical SANFootball IDs remain in metadata/database relationships; Cloudflare-generated IDs may remain provider IDs.

Not every image must live only in Cloudflare Images. R2 remains appropriate for source archives, arbitrary binary objects, processing inputs, or images that do not need the managed Images product. The canonical asset record MUST make the selected product explicit.

---

## 76. MEDIA ACCESS AND DELIVERY SECURITY

Public, unlisted, private, premium, early-access, ad-free, and member-only media MUST have explicit access classes.

### 76.1 Signed delivery

Protected media MUST use short-lived signed URLs, tokens, cookies, or provider playback signatures appropriate to the selected Cloudflare product.

Current baseline:

- protected R2 audio/object -> short-lived `pycflare`-generated R2 GET capability or an explicitly designed Cloudflare edge authorization adapter;
- protected Cloudflare Images -> `requireSignedURLs` plus server-side signing through `pycflare`;
- protected Cloudflare Stream -> `requireSignedURLs` plus a short-lived Stream playback token signed/issued server-side through `pycflare`.

The application should return a playback/media descriptor, not durable origin credentials or bare provider secrets.

Signing keys MUST be stored in a secret manager/environment secret facility, loaded only in server-side infrastructure code, and excluded from model serialization/logging.

### 76.2 Range requests

Audio delivery infrastructure MUST support byte-range/resume behaviour required by podcast clients and seek operations where applicable.

### 76.3 Downloads

Offline/download functionality MUST use entitlement-aware, expiry-aware delivery and must not turn a temporary entitlement into an unintended permanent public URL.

Client-side DRM is not assumed to provide absolute protection; the server must still enforce canonical entitlement at issuance time.

### 76.4 Hotlink/abuse controls

Where materially useful, use signed delivery, token scope, origin restrictions, rate limits, anomaly detection, and bounded validity rather than relying on obscurity.

### 76.5 Cloudflare Stream processing callbacks

Cloudflare Stream processing state MUST be reconciled asynchronously. Configure the account webhook deliberately and verify callbacks over the exact raw request body through the `pycflare` Stream webhook verification surface before parsing/trusting JSON.

Webhook handling MUST be:

- authenticated/verified;
- idempotent;
- tolerant of duplicate/out-of-order events where possible;
- mapped to canonical media processing states;
- observable;
- safe against a provider retry storm.

A client report that an upload finished is never sufficient by itself to mark a Stream asset ready.

---

## 77. APPLICATION COMPUTE AND CONTAINER HOSTING

The production application SHOULD run as immutable containers or an equivalent reproducible deployment unit.

The reference deployment MAY use AWS ECS with Fargate initially to avoid premature Kubernetes operational complexity.

### 77.1 Separate deployables

At minimum support separate process/deployment definitions for:

```text
web/api
realtime if applicable
ordinary worker
media worker
AI/transcript worker
scheduler/beat
administrative one-off jobs/migrations
```

They MAY share one codebase/container image while having different commands, resources, autoscaling, and network permissions.

### 77.2 Resource limits

Define explicit CPU and memory reservations/limits where the platform supports them.

Media workers SHOULD receive different resource profiles from web workers.

### 77.3 Health checks

Expose distinct:

- liveness;
- readiness;
- dependency health information for operators.

Readiness should fail when the instance cannot safely accept traffic, but liveness MUST NOT cause restart loops merely because an optional external provider is unavailable.

### 77.4 Graceful shutdown

Web and worker processes MUST handle termination signals, stop accepting new work, and finish/return in-flight work according to bounded shutdown policy.

### 77.5 Autoscaling

Scale web compute from request/concurrency/latency/CPU/memory signals.

Scale worker pools from backlog/age/processing-time/resource signals.

Never require scaling the web tier simply because video/transcription demand increased.

---

## 78. DATABASE, CACHE, SEARCH, AND ANALYTICS HOSTING

### 78.1 PostgreSQL

Use managed PostgreSQL in production unless an ADR justifies self-management.

Production posture SHOULD include:

- automated backups;
- point-in-time recovery where supported/required;
- encryption in transit and at rest;
- monitoring;
- maintenance strategy;
- tested restore;
- high availability appropriate to the production tier.

Use read replicas only when measured read load, reporting, analytics, or availability requirements justify them. Do not introduce replica-routing complexity prematurely.

### 78.2 Connection pooling

Introduce PgBouncer/RDS Proxy/equivalent before horizontal application scaling can exhaust PostgreSQL connection capacity.

### 78.3 Redis/Valkey

Use managed Redis/Valkey where production reliability requires it.

Suitable uses include:

- caching;
- rate limiting;
- ephemeral session/coordination state where architecture permits;
- locks with carefully defined semantics;
- Celery/broker use if the canonical broker choice selects it.

Do not store canonical subscription, entitlement, episode, or billing truth only in Redis.

### 78.4 Search

Start with PostgreSQL search where it meets measured needs. Extract to OpenSearch/Elasticsearch/Meilisearch/Typesense or another dedicated search engine only behind the canonical search facade when scale/features justify it.

### 78.5 Analytics

High-volume product events SHOULD eventually flow to an OLAP/data-warehouse/data-lake path rather than forcing transactional PostgreSQL to serve raw event analytics indefinitely.

Operational application truth and analytical event history MUST remain separable.

---

## 79. NETWORKING AND SECURITY TOPOLOGY

Production environments SHOULD use private networking for databases, caches, queues, and internal-only services.

### 79.1 Least privilege

Each deployable MUST receive only permissions required for its role.

Examples:

- web can create upload intents but need not have unrestricted bucket administration;
- media workers can read source/write derivatives only within required scopes;
- analytics workers do not need billing mutation rights;
- frontend clients never receive cloud API secrets.

### 79.2 Egress controls

Where practical, restrict/observe outbound access for high-risk workers that fetch remote URLs or process untrusted content.

RSS fetchers and importers MUST continue to enforce SSRF controls irrespective of network perimeter.

### 79.3 Secrets

Use a managed secret store or secure platform injection for production credentials.

Secrets MUST support rotation without source-code changes.

---

## 80. INFRASTRUCTURE AS CODE, CI/CD, AND RELEASES

Production infrastructure MUST be reproducible through Infrastructure as Code.

Terraform is the preferred default; Pulumi or an equivalent is acceptable by ADR.

### 80.1 IaC scope

IaC SHOULD cover:

- networking;
- DNS/edge configuration where supported;
- application services;
- worker services;
- load balancers;
- databases;
- caches;
- queues;
- object storage;
- IAM/service identities;
- alarms/monitoring infrastructure;
- secrets references;
- autoscaling policies.

Manual console changes in production SHOULD be treated as emergency exceptions and reconciled back into code.

### 80.2 Environments

Maintain clear isolation for:

```text
development
staging
production
```

Production credentials/data MUST NOT be copied casually into development environments.

### 80.3 CI/CD

CI SHOULD include:

- formatting/linting;
- static typing where repository policy uses it;
- unit/integration tests;
- security/dependency checks;
- container build;
- migration safety checks;
- IaC validation/plan;
- artifact/image publication;
- controlled deployment.

### 80.4 Deployment strategy

Production deployment SHOULD support rolling or blue/green deployment with health checks and rollback.

Database migrations MUST be backward-compatible across the deployment window when old and new application versions may overlap.

### 80.5 Container provenance

Use immutable image identifiers/digests for production rollouts where practical and retain enough metadata to identify the exact source commit/build deployed.

---

## 81. HIGH AVAILABILITY, BACKUP, AND DISASTER RECOVERY

Cloud durability is not a substitute for an explicit recovery plan.

### 81.1 Database recovery

Define and test:

- automated backup schedule;
- PITR policy where enabled;
- retention;
- restore process;
- recovery validation;
- target RPO;
- target RTO.

### 81.2 Media recovery

For critical originals and irreplaceable creator assets, define a secondary-copy/replication/export policy appropriate to risk and cost.

Processed derivatives that can be regenerated MAY have a weaker backup requirement if regeneration time/cost is acceptable.

### 81.3 Configuration recovery

Git/IaC, container registry, secret-management procedures, DNS configuration, and runbooks are part of disaster recovery.

### 81.4 Regional strategy

Do NOT begin with active-active multi-region database complexity without demonstrated need.

Preferred evolution:

```text
Stage 1: one primary application region + global CDN/media delivery
Stage 2: multi-AZ/high-availability within region
Stage 3: warm standby / cross-region recovery where justified
Stage 4: multi-region application/read strategy if measured need exists
Stage 5: active-active only with a proven data-consistency design
```

### 81.5 Restore drills

A backup that has never been restored is not a validated recovery system.

Schedule restore drills and record outcomes.

---

## 82. FINOPS, COST CONTROL, AND CAPACITY MANAGEMENT

Cost MUST be observable as a first-class production metric.

Track at minimum:

- object storage growth;
- video storage/delivery usage;
- CDN/origin bandwidth;
- application compute;
- worker/media compute;
- database size/IO/connections;
- cache footprint;
- queue volume;
- search infrastructure;
- analytics ingestion/storage;
- AI/transcription/embedding spend.

### 82.1 Cost attribution

Where practical tag/attribute cost to environment and workload class, and to creator/network/tenant for high-cost media features when commercially useful.

### 82.2 Media cost controls

The application SHOULD support:

- upload quotas;
- duration limits;
- maximum source quality where appropriate;
- controlled derivative count;
- lifecycle movement/deletion;
- data-saver variants;
- duplicate detection by checksum/content identity where safe;
- prevention of repeated unnecessary transcodes;
- processing-version awareness;
- configurable video limits.

### 82.3 Cost anomaly detection

Alert on material anomalies such as:

- sudden storage growth;
- origin egress spike;
- video delivery spike;
- runaway transcoding;
- queue retry storms;
- AI/embedding spend spikes.

### 82.4 Build-vs-buy gates

Managed services SHOULD be preferred while engineering/operational simplicity outweighs marginal unit-cost savings.

Self-host media transcoding, search, analytics, or other infrastructure only after documenting:

- current spend;
- projected spend;
- expected savings;
- engineering cost;
- on-call burden;
- reliability risk;
- migration plan;
- rollback strategy.

---

## 83. INFRASTRUCTURE MATURITY STAGES

Do not implement the final-scale topology on day one. Build boundaries early; activate complexity when required.

### Stage I — Launch / early production

```text
Cloudflare edge
pycflare Git-pinned integration
Cloudflare R2 for audio/object storage
Cloudflare Images for managed images
Cloudflare Stream for video
2+ stateless application containers where availability requires
managed PostgreSQL
managed Redis/Valkey or current canonical cache/broker
separate worker processes
basic OpenTelemetry/error monitoring
IaC + CI/CD
backup + restore procedure
```

### Stage II — Growth

Add as measured:

- horizontal autoscaling;
- specialised worker pools;
- DB connection pooling/proxy;
- Multi-AZ/HA posture;
- stronger queue/DLQ operations;
- dedicated search;
- analytics pipeline/warehouse;
- advanced dashboards/alerts;
- formal cost dashboards;
- secondary copy policy for critical originals.

### Stage III — Large scale

Consider only with evidence:

- regional application clusters;
- read replicas/regional reads;
- Kafka or another event-streaming backbone;
- dedicated recommendation infrastructure;
- large OLAP/data lake;
- custom media processing/transcoding fleet;
- GPU workers;
- Kubernetes where operationally justified;
- multi-region disaster recovery;
- partitioning/sharding where database evidence requires it.

The codebase MUST be structured so Stage I can evolve into Stages II/III without changing canonical product/domain semantics.

---

## 84. INFRASTRUCTURE ACCEPTANCE GATES

A production infrastructure change is NOT complete until applicable checks pass.

### Media/upload

- direct upload works without routing full media bytes through Django;
- large upload resume/multipart behaviour is tested;
- incomplete uploads are cleaned;
- invalid media is rejected safely;
- protected playback cannot bypass entitlement;
- source/derivative lineage is recorded;
- `pycflare` is the only normal Python integration path for R2/Images/Stream;
- dependency is pinned to an immutable Git revision and locked;
- R2 production delivery does not depend on `r2.dev`;
- protected R2 audio cannot be fetched without an unexpired capability;
- private Images cannot be fetched without a valid signed URL;
- private Stream playback cannot succeed with only the bare video ID;
- Cloudflare upload/playback/signing secrets never reach the browser bundle or logs;
- Stream webhook verification and replay/idempotency tests pass.

### Compute

- web and workers can scale independently;
- graceful shutdown works;
- health checks distinguish readiness/liveness;
- resource limits are defined;
- media jobs cannot starve web/critical workers.

### Data

- DB backups are enabled and restore tested;
- connection capacity is documented;
- cache failure degrades safely where designed;
- search/analytics outages do not corrupt transactional truth.

### Reliability

- retries are idempotent;
- DLQ/failed-job path is operable;
- queue backlog alerts exist;
- provider outage behaviour is documented;
- rollback exists for deployment/IaC changes.

### Security

- least-privilege service credentials;
- no provider secret in client bundles;
- signed media capability expires;
- origins/internal services are appropriately restricted;
- logs do not expose signed URLs/secrets.

### Observability

- API, DB, cache, queue, worker, media, and provider telemetry exists;
- logs/traces share correlation identifiers;
- high-severity alerts have runbooks;
- cost/storage growth is visible.

### Portability

- domain code does not import provider SDKs directly except in adapter/infrastructure modules;
- provider IDs are not used as canonical domain identifiers;
- a migration/export strategy exists for durable provider-hosted media.

---

## 85. PRODUCT PRIORITY ORDER

Unless dependency analysis materially changes the sequence, priority should remain:

### Highest immediate value

1. Advanced Player
2. Smart Library
3. Smart Downloads
4. Cross-Device Playback
5. RSS/OPML Portability

### High growth and differentiation

6. Clips
7. Quote Cards
8. Video Podcasts
9. Creator Analytics
10. Semantic Transcript Search
11. Football Entity Intelligence
12. Entity-Aware Notifications
13. Personalised Football Home

### Platform and creator expansion

14. Networks/Channels
15. Creator Teams
16. Ad-Free/Premium Media Variants
17. Subscription Conversion Analytics
18. Highlights Feed

### Football-native differentiation

19. Live Podcasting
20. Matchday Rooms
21. Match-Aware Chapters
22. Listen Around the Match

### Engagement and ecosystem

23. Listener Stats
24. Annual Recap
25. Achievements
26. Connected Devices
27. Transcript Translation
28. Creator AI

---

## 86. FINAL AGENT DIRECTIVE

SanFootball has already suffered the natural consequence of long-lived feature growth: capabilities arrived at different stages, overlapping responsibilities emerged, and the codebase became harder to reason about.

The refactor exists to correct that.

This feature-expansion specification MUST NOT undo it.

When adding a feature, the implementation agent must repeatedly ask:

```text
Which canonical domain owns this?
```

```text
Which existing model/service can be extended?
```

```text
Am I creating a second source of truth?
```

```text
Can this heavy work be moved out of the request path?
```

```text
How will this fail?
```

```text
How will this be retried?
```

```text
How will this be authorised?
```

```text
How will this be observed?
```

```text
How will this be migrated?
```

```text
What obsolete implementation can now be deleted?
```

The goal is not to ship the largest possible number of features.

The goal is to build a coherent, fast, secure, highly scalable, production-grade football podcast platform whose architecture remains understandable as the product expands.

The intended differentiation is:

```text
Generic podcast platforms:
    podcast → listener

SanFootball:
    football event
        ↕
    club / player / competition
        ↕
    podcast / episode / moment
        ↕
    creator / community / listener
        ↕
    subscription / live / discovery
```

Every implementation decision should strengthen that model while preserving simplicity, canonical ownership, data integrity, security, performance, and maintainability.

**This file is an execution contract. Read it completely, inspect the repository completely, implement incrementally, test every layer, document decisions, preserve data, migrate callers, delete superseded code, and never recreate duplicate systems that the modernisation effort was designed to eliminate.**

---

# PART III — UNIFIED FINAL DIRECTIVE

This single file is the repository authority. The coding agent must not require any of the superseded SANFootball AGENTS specifications in order to proceed.

For every change, answer these questions before completion:

```text
Which canonical domain owns this?
Which existing model/service/policy/selector can be extended?
Am I creating a second source of truth?
Is the state transition explicit and transaction-safe?
Is authorisation enforced server-side?
Can heavy work be moved off the request path?
Is retryable work idempotent?
How does this behave under concurrency and partial failure?
How is backpressure handled?
How is it observed and alerted on?
How is it deployed and rolled back?
Does it depend on durable local disk?
Can web and worker workloads scale independently?
Does media bypass Django byte transport where appropriate?
Are provider-specific concerns behind adapters?
How are secrets, privacy, retention, backup, and restore handled?
How does storage, bandwidth, compute, or provider cost grow?
How is existing data migrated and verified?
Which obsolete implementation can now be deleted?
What tests prove the feature and migration are correct?
What documentation and ADR updates are required?
```

**Read this file completely. Inspect the repository completely. Preserve data. Preserve intentional compatibility. Canonicalise before extending. Build incrementally. Keep production infrastructure in view from the start. Test every layer. Document architecture and operations. Observe failures. Control cost. Delete superseded code. Never recreate the duplicate systems this programme exists to eliminate.**
