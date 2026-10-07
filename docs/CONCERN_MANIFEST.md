# Concern Manifest

Total concerns: 46

## SF-00 — Baseline & Repository Characterization
- File: `agents/SF-00_baseline_repository_characterization.md`
- Dependencies: none
- Objective: Create a trustworthy repository baseline and map the existing system before any invasive implementation work.

## SF-01 — Characterization Test Safety Net
- File: `agents/SF-01_characterization_test_safety_net.md`
- Dependencies: SF-00
- Objective: Lock down valuable current behavior before replacing legacy implementations, without freezing known defects as desired behavior.

## SF-02 — Settings, Secrets & Environment Configuration
- File: `agents/SF-02_settings_secrets_environment.md`
- Dependencies: SF-00
- Objective: Make environment selection, secrets, security settings and production configuration explicit and deterministic.

## SF-03 — Dependency, Runtime & Process Isolation
- File: `agents/SF-03_dependency_runtime_process_isolation.md`
- Dependencies: SF-02
- Objective: Separate lightweight web runtime concerns from heavy media, transcription, ML and worker workloads.

## SF-04 — Legacy Framework & API Structure Removal
- File: `agents/SF-04_legacy_framework_api_structure.md`
- Dependencies: SF-01, SF-02
- Objective: Remove obsolete framework wiring and flatten API/application structure without breaking stable contracts.

## SF-05 — Identity, Authentication & Authorization Foundation
- File: `agents/SF-05_identity_authentication_authorization.md`
- Dependencies: SF-01, SF-02
- Objective: Establish one coherent identity mapping and explicit authentication/authorization behavior.

## SF-06 — Podcast Content & Sports Metadata Canonicalization
- File: `agents/SF-06_podcast_content_sports_metadata.md`
- Dependencies: SF-04
- Objective: Converge Podcast/Season/Episode and football metadata on one canonical content model with safe migration.

## SF-07 — Plan, Price, Subscription & Entitlement Models
- File: `agents/SF-07_membership_commercial_models.md`
- Dependencies: SF-05, SF-06
- Objective: Create one coherent commercial-state model before access or billing logic builds on it.

## SF-08 — Canonical Access Policy
- File: `agents/SF-08_canonical_access_policy.md`
- Dependencies: SF-07
- Objective: Centralize all protected-resource authorization in one server-side AccessPolicy with structured decisions.

## SF-09 — Billing Provider & Webhook Lifecycle
- File: `agents/SF-09_billing_webhook_lifecycle.md`
- Dependencies: SF-08
- Objective: Reduce billing to a small provider-integration domain with replay-safe subscription reconciliation.

## SF-10 — Playback Progress & Continue Listening
- File: `agents/SF-10_playback_progress_continue_listening.md`
- Dependencies: SF-05, SF-06
- Objective: Create one canonical playback-progress state and selector foundation for later player/session features.

## SF-11 — Queue / Up Next Rewrite
- File: `agents/SF-11_queue_up_next.md`
- Dependencies: SF-10
- Objective: Replace overlapping queue/order state with one transactional ordered queue model and service.

## SF-12 — Library: Follows, Playlists & Bookmarks
- File: `agents/SF-12_library_follows_playlists_bookmarks.md`
- Dependencies: SF-10, SF-11
- Objective: Separate persistent library intent from queue and commercial subscription state.

## SF-13 — Media Asset Model & Cloudflare Provider Boundary
- File: `agents/SF-13_media_asset_cloudflare_boundary.md`
- Dependencies: SF-03, SF-06, SF-08
- Objective: Establish provider-neutral media ownership with Cloudflare-backed production adapters through pycflare only.

## SF-14 — Direct Upload, Protected Delivery & Media Lifecycle
- File: `agents/SF-14_direct_upload_protected_delivery_lifecycle.md`
- Dependencies: SF-13, SF-08
- Objective: Make large-media upload, protected playback/download and lifecycle operations production-safe.

## SF-15 — Transcription, Chapters, Summaries & AI Baseline
- File: `agents/SF-15_transcription_chapters_ai_baseline.md`
- Dependencies: SF-13
- Objective: Canonicalize transcript/chapter/summary state and isolate heavy processing before advanced semantic features.

## SF-16 — Community & Moderation
- File: `agents/SF-16_community_moderation.md`
- Dependencies: SF-05, SF-06
- Objective: Converge comments/replies/reactions/polls on one moderated community system.

## SF-17 — Analytics Events & Transactional Publication
- File: `agents/SF-17_analytics_events_transactional_publication.md`
- Dependencies: SF-05, SF-06
- Objective: Separate current state from event history and establish reliable internal-event publication.

## SF-18 — Discovery, Search, Recommendation & Editorial
- File: `agents/SF-18_discovery_search_recommendation_editorial.md`
- Dependencies: SF-06, SF-12, SF-17
- Objective: Converge discovery onto one bounded, explainable, football-aware recommendation/search/home composition architecture.

## SF-19 — Offline / Downloads & Legacy DRM De-risking
- File: `agents/SF-19_offline_download_drm_derisking.md`
- Dependencies: SF-08, SF-14
- Objective: Preserve legitimate offline capability while retiring unsafe or disproportionate custom DRM paths.

## SF-20 — Core Refactor Hardening Gate
- File: `agents/SF-20_core_refactor_hardening_gate.md`
- Dependencies: SF-02, SF-03, SF-04, SF-05, SF-06, SF-07, SF-08, SF-09, SF-10, SF-11, SF-12, SF-13, SF-14, SF-15, SF-16, SF-17, SF-18, SF-19
- Objective: Verify that the canonicalisation programme is actually complete enough to become the baseline for feature expansion.

## SF-21 — Application Compute & Worker Topology
- File: `agents/SF-21_application_compute_worker_topology.md`
- Dependencies: SF-20
- Objective: Make web and worker compute stateless, independently scalable and resource-isolated.

## SF-22 — Database, Cache, Broker & Search Hosting
- File: `agents/SF-22_database_cache_broker_search_hosting.md`
- Dependencies: SF-20
- Objective: Define production-safe data-service capacity, connection and degradation behavior.

## SF-23 — Edge, CDN & Object-Storage Security
- File: `agents/SF-23_edge_cdn_object_storage_security.md`
- Dependencies: SF-14, SF-20
- Objective: Harden edge delivery, origin protection and Cloudflare media paths for production.

## SF-24 — Networking, Secrets & Least Privilege
- File: `agents/SF-24_networking_secrets_least_privilege.md`
- Dependencies: SF-21, SF-22, SF-23
- Objective: Apply least-privilege network and credential boundaries to application, workers and providers.

## SF-25 — IaC, CI/CD, Releases & Environments
- File: `agents/SF-25_iac_cicd_releases_environments.md`
- Dependencies: SF-21, SF-22, SF-23, SF-24
- Objective: Make production infrastructure and releases reproducible, reviewable and rollback-capable.

## SF-26 — Backup, Restore & Disaster Recovery
- File: `agents/SF-26_backup_restore_disaster_recovery.md`
- Dependencies: SF-22, SF-25
- Objective: Turn backup claims into tested recovery procedures with explicit RPO/RTO.

## SF-27 — Observability, Reliability, Capacity & FinOps
- File: `agents/SF-27_observability_reliability_capacity_finops.md`
- Dependencies: SF-21, SF-22, SF-23
- Objective: Make failures, performance, capacity and cost visible enough to operate the platform safely.

## SF-28 — Production Infrastructure Acceptance Gate
- File: `agents/SF-28_production_infrastructure_acceptance_gate.md`
- Dependencies: SF-21, SF-22, SF-23, SF-24, SF-25, SF-26, SF-27
- Objective: Approve the minimum production-safe infrastructure foundation before growth features proceed.

## SF-29 — Advanced Player
- File: `agents/SF-29_advanced_player.md`
- Dependencies: SF-28
- Objective: Add advanced playback controls without creating duplicate progress or entitlement state.

## SF-30 — Smart Library & Smart Downloads
- File: `agents/SF-30_smart_library_downloads.md`
- Dependencies: SF-29
- Objective: Add rule-driven library and download behavior while preserving canonical queue/download ownership.

## SF-31 — Cross-Device Playback & Active Session
- File: `agents/SF-31_cross_device_playback.md`
- Dependencies: SF-30
- Objective: Synchronize playback across devices through one active playback session with explicit concurrency semantics.

## SF-32 — RSS & OPML Portability
- File: `agents/SF-32_rss_opml_portability.md`
- Dependencies: SF-31
- Objective: Support safe import/export and external feed subscriptions without weakening network security.

## SF-33 — Clips & Quote Cards
- File: `agents/SF-33_clips_quote_cards.md`
- Dependencies: SF-32
- Objective: Create shareable moments while preserving source linkage, permissions and premium boundaries.

## SF-34 — Video Podcasts & Media Variants
- File: `agents/SF-34_video_podcasts.md`
- Dependencies: SF-33
- Objective: Extend canonical media to video with scalable ingest, adaptive private delivery and audio/video synchronization.

## SF-35 — Football Intelligence & Content Knowledge Graph
- File: `agents/SF-35_football_intelligence_knowledge_graph.md`
- Dependencies: SF-34
- Objective: Link transcript moments and content to canonical football entities with provenance and human-correctable extraction.

## SF-36 — Semantic Search / Ask SANFootball
- File: `agents/SF-36_semantic_search_ask_sanfootball.md`
- Dependencies: SF-35
- Objective: Add entitlement-aware retrieval over transcript chunks before any optional grounded generation.

## SF-37 — Intelligent Notifications, Personalised Home & Highlights
- File: `agents/SF-37_notifications_personalized_home_highlights.md`
- Dependencies: SF-36
- Objective: Turn canonical follows, entities and discovery signals into deduplicated notifications and personalised football discovery.

## SF-38 — Creator & Subscription Conversion Analytics
- File: `agents/SF-38_creator_conversion_analytics.md`
- Dependencies: SF-37
- Objective: Provide creator-facing retention, replay, drop-off and conversion analytics without compromising privacy or transactional performance.

## SF-39 — Networks, Creator Teams & Advanced Commercial Packaging
- File: `agents/SF-39_networks_teams_commercial_packaging.md`
- Dependencies: SF-38
- Objective: Add network ownership, creator collaboration and bundled commercial packaging without fragmenting authorization.

## SF-40 — Live Podcasting
- File: `agents/SF-40_live_podcasting.md`
- Dependencies: SF-39
- Objective: Implement a fault-tolerant live-broadcast lifecycle that can become a normal canonical episode.

## SF-41 — Matchday Rooms, Chapters & Listen-Around-the-Match
- File: `agents/SF-41_matchday_experience.md`
- Dependencies: SF-40
- Objective: Build football-native match experiences by composing existing live, community, entity, chapter and queue primitives.

## SF-42 — Listener Stats, Annual Recap & Achievements
- File: `agents/SF-42_listener_engagement.md`
- Dependencies: SF-41
- Objective: Create privacy-aware listener insights and shareable recap/achievement experiences from canonical analytics.

## SF-43 — Connected Devices & Low-Bandwidth Experience
- File: `agents/SF-43_connected_devices_low_bandwidth.md`
- Dependencies: SF-42
- Objective: Extend canonical playback safely to casting/TV/automotive/speakers/wearables while supporting constrained networks.

## SF-44 — Transcript Translation, Accessibility & Creator AI
- File: `agents/SF-44_translation_accessibility_creator_ai.md`
- Dependencies: SF-43
- Objective: Add accessible multilingual transcript experiences and creator-assistive AI with explicit provenance and human approval.

## SF-45 — Final System Hardening, End-to-End Acceptance & Cleanup
- File: `agents/SF-45_final_system_hardening_acceptance_cleanup.md`
- Dependencies: SF-44
- Objective: Run the unified acceptance programme, remove superseded code and leave the repository in a coherent production-ready state.
