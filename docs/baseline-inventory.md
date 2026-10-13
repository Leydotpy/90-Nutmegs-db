# SF-00 baseline evidence inventory

Snapshot of `e24ff2e9c9ae7ecb563215f1cfc4f1b6e6687c6e`, inspected 2026-10-11 with Python 3.14.8 and `conf.settings.test`. This is an architecture appendix, not an implementation tracker. Findings and approvals belong in [the ledger](../SANFOOTBALL_IMPLEMENTATION_STATUS.md).

Runtime metadata is from Django app/model/URL registries; migration declarations and task/receiver/test definitions are read from source. No production database or provider is queried. Implicit M2M through tables are represented by the owning relation, not separate rows. Reverse ORM accessors are derivable from the listed forward relations.

## Installed app registrations

| Label | Module | Classification |
|---|---|---|
| `admin` | `django.contrib.admin` | dependency |
| `auth` | `django.contrib.auth` | dependency |
| `contenttypes` | `django.contrib.contenttypes` | dependency |
| `sessions` | `django.contrib.sessions` | dependency |
| `messages` | `django.contrib.messages` | dependency |
| `staticfiles` | `django.contrib.staticfiles` | dependency |
| `sites` | `django.contrib.sites` | dependency |
| `flatpages` | `django.contrib.flatpages` | dependency |
| `guardian` | `guardian` | dependency |
| `django_filters` | `django_filters` | dependency |
| `corsheaders` | `corsheaders` | dependency |
| `rest_framework` | `rest_framework` | dependency |
| `django_clerk_sdk` | `django_clerk_sdk` | dependency |
| `users` | `django_clerk_sdk.users` | dependency |
| `django_celery_results` | `django_celery_results` | dependency |
| `django_celery_beat` | `django_celery_beat` | dependency |
| `drf_spectacular` | `drf_spectacular` | dependency |
| `drf_spectacular_sidecar` | `drf_spectacular_sidecar` | dependency |
| `pycflare_django` | `pycflare.django` | dependency |
| `api` | `api` | repository |
| `rest` | `api.rest` | repository |
| `dashboard_api` | `api.rest.dashboard` | repository |
| `dashboard_apps_api` | `api.rest.dashboard.apps` | repository |
| `match_dashboard_api` | `api.rest.dashboard.apps.match` | repository |
| `persons_dashboard_api` | `api.rest.dashboard.apps.persons` | repository |
| `podcasts_dashboard_api` | `api.rest.dashboard.apps.podcasts` | repository |
| `promotions_dashboard_api` | `api.rest.dashboard.apps.promotions` | repository |
| `region_dashboard_api` | `api.rest.dashboard.apps.region` | repository |
| `membership_dashboard_api` | `api.rest.dashboard.apps.memberships` | repository |
| `rest_web` | `api.rest.web` | repository |
| `api_apps` | `api.rest.web.apps` | repository |
| `comment_web_api` | `api.rest.web.apps.comments` | repository |
| `media_web_api` | `api.rest.web.apps.media` | repository |
| `media_audio_api` | `api.rest.web.apps.media.audio` | repository |
| `media_offline_web_api` | `api.rest.web.apps.media.offline` | repository |
| `media_streaming_web_api` | `api.rest.web.apps.media.streaming` | repository |
| `podcast_web_api` | `api.rest.web.apps.podcasts` | repository |
| `profile_web_api` | `api.rest.web.apps.profile` | repository |
| `queue_web_api` | `api.rest.web.apps.queue` | repository |
| `accounts` | `apps.accounts` | repository |
| `analytics` | `apps.analytics` | repository |
| `billing` | `apps.billing` | repository |
| `category` | `apps.category` | repository |
| `comments` | `apps.comments` | repository |
| `match` | `apps.match` | repository |
| `media` | `apps.media` | repository |
| `audio` | `apps.media.audio` | repository |
| `chapters` | `apps.media.chapters` | repository |
| `images` | `apps.media.images` | repository |
| `offline` | `apps.media.offline` | repository |
| `transcription` | `apps.media.transcription` | repository |
| `video` | `apps.media.video` | repository |
| `forum` | `apps.forum` | repository |
| `posts` | `apps.posts` | repository |
| `persons` | `apps.persons` | repository |
| `region` | `apps.region` | repository |
| `podcasts` | `apps.posts.podcasts` | repository |
| `polls` | `apps.posts.polls` | repository |
| `memberships` | `apps.memberships` | repository |
| `promotions` | `apps.promotions` | repository |
| `queue` | `apps.queue` | repository |
| `recommendation` | `apps.recommendation` | repository |
| `ml` | `apps.recommendation.ml` | repository |
| `leagues` | `apps.region.leagues` | repository |
| `clubs` | `apps.region.leagues.clubs` | repository |
| `thumbnail` | `apps.thumbnail` | repository |
| `tactics` | `apps.tactics` | repository |

## Repository model and relation map

All registered repository models, including proxy models. Unique scalar fields, `unique_together`, explicit constraints and explicit indexes are included; foreign keys also receive Django default indexes. Generic relations are described as generic targets, not enforced foreign keys. Admin indicates current `admin.site` registration.

| Model / source | Forward and generic relations | Uniqueness / constraints / indexes | Admin |
|---|---|---|---|
| `analytics.ObjectView` — `app/apps/analytics/models.py` | user → users.ClerkUser (ForeignKey, SET_NULL, nullable); content_type → contenttypes.ContentType (ForeignKey, CASCADE); content_object → generic content type/object ID (GenericForeignKey) | index <Index: fields=['user', 'content_type'] name='analytics_o_user_id_b54e33_idx'>; index <Index: fields=['content_type', 'object_id', 'ip_address', 'timestamp'] name='analytics_o_content_ad4cf6_idx'> | yes |
| `billing.Transaction` — `app/apps/billing/models.py` | source → billing.Source (ForeignKey, CASCADE) | index <Index: fields=['source', 'status'] name='billing_tra_source__f7ded8_idx'>; index <Index: fields=['reference', 'amount'] name='billing_tra_referen_ea57c6_idx'> | yes |
| `billing.Source` — `app/apps/billing/models.py` | order → memberships.Entitlement (ForeignKey, CASCADE); source_type → billing.SourceType (ForeignKey, CASCADE) | — | yes |
| `billing.SourceType` — `app/apps/billing/models.py` | — | unique code | yes |
| `billing.Bankcard` — `app/apps/billing/models.py` | user → users.ClerkUser (ForeignKey, CASCADE) | — | yes |
| `category.Category` — `app/apps/category/models.py` | tier → memberships.Plan (ForeignKey, CASCADE) | unique slug | yes |
| `comments.Comment` — `app/apps/comments/models.py` | user → users.ClerkUser (ForeignKey, CASCADE); content_type → contenttypes.ContentType (ForeignKey, CASCADE); parent → comments.Comment (ForeignKey, CASCADE, nullable); content_object → generic content type/object ID (GenericForeignKey) | index <Index: fields=['content_type', 'object_id', 'timestamp'] name='comments_co_content_01c7c5_idx'>; index <Index: fields=['user', 'timestamp'] name='comments_co_user_id_d6862b_idx'> | yes |
| `match.Shot` — `app/apps/match/models.py` | team → clubs.Team (ForeignKey, CASCADE); player → persons.Player (ForeignKey, SET_NULL, nullable) | — | yes |
| `match.Foul` — `app/apps/match/models.py` | team → clubs.Team (ForeignKey, CASCADE); player → persons.Player (ForeignKey, SET_NULL, nullable) | — | yes |
| `match.SetPiece` — `app/apps/match/models.py` | team → clubs.Team (ForeignKey, CASCADE) | — | yes |
| `match.Goal` — `app/apps/match/models.py` | team → clubs.Team (ForeignKey, CASCADE); scorer → persons.Player (ForeignKey, CASCADE); assist → persons.Player (ForeignKey, SET_NULL, nullable); scorer_experimental → tactics.LineUp (ForeignKey, CASCADE); assist_experimental → tactics.LineUp (ForeignKey, SET_NULL, nullable) | — | yes |
| `match.TeamPossession` — `app/apps/match/models.py` | team → clubs.Team (ForeignKey, CASCADE) | — | yes |
| `match.Possession` — `app/apps/match/models.py` | home → match.TeamPossession (ForeignKey, CASCADE); away → match.TeamPossession (ForeignKey, CASCADE) | — | yes |
| `match.Match` — `app/apps/match/models.py` | home_team → clubs.Team (ForeignKey, CASCADE); away_team → clubs.Team (ForeignKey, CASCADE); venue → clubs.Stadium (ForeignKey, SET_NULL, nullable); competition → leagues.League (ForeignKey, CASCADE); campaign → leagues.Campaign (ForeignKey, CASCADE) | — | yes |
| `match.Highlight` — `app/apps/match/models.py` | video_ptr → video.Video (OneToOneField, CASCADE); match → match.Match (ForeignKey, CASCADE) | — | yes |
| `match.Substitution` — `app/apps/match/models.py` | team → clubs.Team (ForeignKey, CASCADE); player_out → persons.Player (ForeignKey, CASCADE); player_in → persons.Player (ForeignKey, CASCADE) | — | yes |
| `match.Booking` — `app/apps/match/models.py` | player → persons.Player (ForeignKey, CASCADE); team → clubs.Team (ForeignKey, CASCADE) | — | yes |
| `match.Event` — `app/apps/match/models.py` | match → match.Match (OneToOneField, CASCADE); possession → match.Possession (OneToOneField, CASCADE); bookings → match.Booking (ManyToManyField, through=match.Event_bookings); substitutions → match.Substitution (ManyToManyField, through=match.Event_substitutions); shots → match.Shot (ManyToManyField, through=match.Event_shots); set_piece → match.SetPiece (ManyToManyField, through=match.Event_set_piece); fouls → match.Foul (ManyToManyField, through=match.FoulEvent); goals → match.Goal (ManyToManyField, through=match.GoalEvent) | unique match; unique possession | yes |
| `match.GoalEvent` — `app/apps/match/models.py` | event → match.Event (ForeignKey, CASCADE); goal → match.Goal (ForeignKey, CASCADE) | — | no |
| `match.FoulEvent` — `app/apps/match/models.py` | event → match.Event (ForeignKey, CASCADE); foul → match.Foul (ForeignKey, CASCADE) | — | no |
| `media.MediaAsset` — `app/apps/media/canonical.py` | created_by → users.ClerkUser (ForeignKey, SET_NULL, nullable); source_asset → media.MediaAsset (ForeignKey, PROTECT, nullable) | constraint <CheckConstraint: condition=(OR: ('source_asset__isnull', True), (NOT (AND: ('id', F(source_asset_id))))) name='media_asset_source_not_self'>; constraint <UniqueConstraint: fields=('created_by', 'upload_idempotency_key') name='media_asset_creator_idempotency_uniq' condition=(AND: (NOT (AND: ('upload_idempotency_key', ''))), ('created_by__isnull', False))>; index <Index: fields=['status', 'created_at'] name='media_asset_status_created_idx'>; index <Index: fields=['media_type', 'access_class'] name='media_asset_type_access_idx'> | no |
| `media.MediaLocation` — `app/apps/media/canonical.py` | asset → media.MediaAsset (ForeignKey, CASCADE) | constraint <UniqueConstraint: fields=('provider', 'product', 'container', 'locator') name='media_loc_provider_object_uniq'>; constraint <UniqueConstraint: fields=('asset',) name='media_location_one_primary_per_asset' condition=(AND: ('is_primary', True))>; index <Index: fields=['asset', 'status'] name='media_loc_asset_status_idx'> | no |
| `media.MediaVariant` — `app/apps/media/canonical.py` | episode → podcasts.Episode (ForeignKey, CASCADE, nullable); asset → media.MediaAsset (ForeignKey, PROTECT) | constraint <UniqueConstraint: fields=('episode', 'asset', 'kind') name='media_variant_episode_asset_kind_uniq' condition=(AND: ('episode__isnull', False))>; index <Index: fields=['episode', 'kind', 'status'] name='media_variant_ep_kind_idx'> | no |
| `media.MediaSettings` — `app/apps/media/models.py` | user → users.ClerkUser (OneToOneField, CASCADE) | unique user | yes |
| `media.PlayList` — `app/apps/media/models.py` | user → users.ClerkUser (ForeignKey, CASCADE, nullable); items → podcasts.Episode (ManyToManyField, through=media.PlaylistItem); categories → category.Category (ManyToManyField, through=media.PlayList_categories) | unique slug | yes |
| `media.PlaylistItem` — `app/apps/media/models.py` | playlist → media.PlayList (ForeignKey, CASCADE); episode → podcasts.Episode (ForeignKey, CASCADE) | unique_together ('playlist', 'episode') | no |
| `audio.Audio` — `app/apps/media/audio/models.py` | episode → podcasts.Episode (ForeignKey, CASCADE) | constraint <UniqueConstraint: fields=('episode',) name='unique_master_per_episode' condition=(AND: ('master', True))>; constraint <UniqueConstraint: fields=('episode', 'quality') name='unique_episode_quality'>; index <Index: fields=['episode', 'quality'] name='audio_audio_episode_a0113f_idx'> | yes |
| `chapters.Chapter` — `app/apps/media/chapters/models.py` | episode → podcasts.Episode (ForeignKey, CASCADE) | — | yes |
| `images.Image` — `app/apps/media/images/models.py` | content_type → contenttypes.ContentType (ForeignKey, CASCADE); content_object → generic content type/object ID (GenericForeignKey) | index <Index: fields=['content_type', 'object_id', 'timestamp'] name='images_imag_content_a396cb_idx'> | yes |
| `offline.Package` — `app/apps/media/offline/models.py` | episode → podcasts.Episode (ForeignKey, CASCADE); created_by → users.ClerkUser (ForeignKey, SET_NULL, nullable) | index <Index: fields=['episode', 'preset'] name='offline_pac_episode_0ce651_idx'> | yes |
| `offline.License` — `app/apps/media/offline/models.py` | package → offline.Package (ForeignKey, CASCADE); user → users.ClerkUser (ForeignKey, CASCADE); device → offline.Device (ForeignKey, CASCADE) | index <Index: fields=['device', 'package'] name='offline_lic_device__c13c46_idx'>; index <Index: fields=['user', 'expires_at'] name='offline_lic_user_id_b5b9fa_idx'> | yes |
| `offline.Device` — `app/apps/media/offline/models.py` | user → users.ClerkUser (ForeignKey, CASCADE) | unique_together ('user', 'device_id'); index <Index: fields=['user', 'device_id'] name='offline_dev_user_id_6d4bc7_idx'> | yes |
| `offline.Packaging` — `app/apps/media/offline/models.py` | episode → podcasts.Episode (ForeignKey, CASCADE); user → users.ClerkUser (ForeignKey, SET_NULL, nullable); package → offline.Package (ForeignKey, SET_NULL, nullable) | index <Index: fields=['episode', 'status'] name='offline_pac_episode_ae4bff_idx'>; index <Index: fields=['user', 'status'] name='offline_pac_user_id_cc7a3c_idx'> | yes |
| `transcription.Transcription` — `app/apps/media/transcription/models.py` | episode → podcasts.Episode (OneToOneField, CASCADE) | unique episode | yes |
| `transcription.TranscriptionBillingRecord` — `app/apps/media/transcription/models.py` | episode → podcasts.Episode (ForeignKey, CASCADE) | — | yes |
| `transcription.UserTranscriptionQuota` — `app/apps/media/transcription/models.py` | user → users.ClerkUser (OneToOneField, CASCADE) | unique user | yes |
| `video.Video` — `app/apps/media/video/models.py` | — | — | yes |
| `forum.Discussion` — `app/apps/forum/models.py` | user → users.ClerkUser (ForeignKey, CASCADE); participants → users.ClerkUser (ManyToManyField, through=forum.Discussion_participants); views → users.ClerkUser (ManyToManyField, through=forum.Discussion_views) | — | yes |
| `forum.Reply` — `app/apps/forum/models.py` | thread → forum.Discussion (ForeignKey, SET_NULL, nullable); user → users.ClerkUser (ForeignKey, CASCADE) | — | no |
| `posts.PostReaction` — `app/apps/posts/models.py` | content_type → contenttypes.ContentType (ForeignKey, CASCADE); user → users.ClerkUser (ForeignKey, CASCADE); content_object → generic content type/object ID (GenericForeignKey) | index <Index: fields=['content_type', 'object_id'] name='posts_postr_content_e91cc9_idx'>; index <Index: fields=['user', 'timestamp'] name='posts_postr_user_id_c6ec2b_idx'> | yes |
| `posts.Post` — `app/apps/posts/models.py` | parent → posts.Post (ForeignKey, SET_NULL, nullable); poll → polls.Poll (ForeignKey, CASCADE, nullable); countries → region.Country (ManyToManyField, through=posts.Post_countries); competitions → leagues.League (ManyToManyField, through=posts.Post_competitions); regions → region.Region (ManyToManyField, through=posts.Post_regions); teams → clubs.Team (ManyToManyField, through=posts.Post_teams); players → persons.Player (ManyToManyField, through=posts.Post_players); matches → match.Match (ManyToManyField, through=posts.Post_matches); subscribers → users.ClerkUser (ManyToManyField, through=posts.Post_subscribers); view_logs → analytics.ObjectView (GenericRelation, DO_NOTHING, nullable) | — | yes |
| `persons.InjuryType` — `app/apps/persons/models.py` | — | — | yes |
| `persons.Injury` — `app/apps/persons/models.py` | injury → persons.InjuryType (ForeignKey, CASCADE) | — | yes |
| `persons.Fitness` — `app/apps/persons/models.py` | player → persons.Player (OneToOneField, CASCADE); injuries → persons.Injury (ManyToManyField, through=persons.Fitness_injuries) | unique player | yes |
| `persons.Player` — `app/apps/persons/models.py` | nations → region.Country (ManyToManyField, through=persons.Player_nations); teams → clubs.Team (ManyToManyField, through=persons.PlayerTransfer) | — | yes |
| `persons.Staff` — `app/apps/persons/models.py` | nations → region.Country (ManyToManyField, through=persons.Staff_nations); teams → clubs.Team (ManyToManyField, through=persons.StaffTransfer) | — | yes |
| `persons.Contract` — `app/apps/persons/models.py` | — | — | no |
| `persons.PlayerTransfer` — `app/apps/persons/models.py` | player → persons.Player (ForeignKey, CASCADE); team → clubs.Team (ForeignKey, SET_NULL, nullable); contract → persons.Contract (ForeignKey, SET_NULL, nullable) | — | no |
| `persons.StaffTransfer` — `app/apps/persons/models.py` | staff → persons.Staff (ForeignKey, CASCADE); team → clubs.Team (ForeignKey, SET_NULL, nullable); contract → persons.Contract (ForeignKey, SET_NULL, nullable) | — | no |
| `region.Region` — `app/apps/region/models.py` | — | unique code | yes |
| `region.Country` — `app/apps/region/models.py` | region → region.Region (ForeignKey, CASCADE) | unique code | yes |
| `podcasts.Podcast` — `app/apps/posts/podcasts/models.py` | parent → podcasts.Podcast (ForeignKey, SET_NULL, nullable); countries → region.Country (ManyToManyField, through=podcasts.Podcast_countries); competitions → leagues.League (ManyToManyField, through=podcasts.Podcast_competitions); regions → region.Region (ManyToManyField, through=podcasts.Podcast_regions); teams → clubs.Team (ManyToManyField, through=podcasts.Podcast_teams); players → persons.Player (ManyToManyField, through=podcasts.Podcast_players); matches → match.Match (ManyToManyField, through=podcasts.Podcast_matches); subscribers → users.ClerkUser (ManyToManyField, through=podcasts.Podcast_subscribers); categories → category.Category (ManyToManyField, through=podcasts.Podcast_categories); view_logs → analytics.ObjectView (GenericRelation, DO_NOTHING, nullable) | unique slug; index <Index: fields=['status', 'published_at'] name='podcast_public_idx'> | yes |
| `podcasts.Season` — `app/apps/posts/podcasts/models.py` | podcast → podcasts.Podcast (ForeignKey, CASCADE); legacy_podcast → podcasts.Podcast (OneToOneField, SET_NULL, nullable) | unique legacy_podcast; constraint <UniqueConstraint: fields=('podcast', 'slug') name='podcast_season_slug_uniq'>; constraint <UniqueConstraint: fields=('podcast', 'position') name='podcast_season_position_uniq'>; constraint <UniqueConstraint: fields=('podcast', 'number') name='podcast_season_number_uniq' condition=(AND: ('number__isnull', False))>; constraint <CheckConstraint: condition=(AND: ('position__gte', 1)) name='podcast_season_position_positive'>; constraint <CheckConstraint: condition=(OR: ('number__isnull', True), ('number__gte', 1)) name='podcast_season_number_positive'>; index <Index: fields=['podcast', 'published_at'] name='podcast_season_public_idx'> | yes |
| `podcasts.Episode` — `app/apps/posts/podcasts/models.py` | podcast → podcasts.Podcast (ForeignKey, CASCADE); season → podcasts.Season (ForeignKey, SET_NULL, nullable); required_plan → memberships.Plan (ForeignKey, SET_NULL, nullable); countries → region.Country (ManyToManyField, through=podcasts.Episode_countries); competitions → leagues.League (ManyToManyField, through=podcasts.Episode_competitions); regions → region.Region (ManyToManyField, through=podcasts.Episode_regions); teams → clubs.Team (ManyToManyField, through=podcasts.Episode_teams); players → persons.Player (ManyToManyField, through=podcasts.Episode_players); matches → match.Match (ManyToManyField, through=podcasts.Episode_matches); subscribers → users.ClerkUser (ManyToManyField, through=podcasts.Episode_subscribers); categories → category.Category (ManyToManyField, through=podcasts.Episode_categories); view_logs → analytics.ObjectView (GenericRelation, DO_NOTHING, nullable) | unique slug; index <Index: fields=['status', 'public_available_at'] name='podcast_ep_public_idx'>; index <Index: fields=['status', 'visibility', 'premium_available_at'] name='podcast_ep_access_idx'>; index <Index: fields=['podcast', 'season', 'published_at'] name='podcast_ep_timeline_idx'> | yes |
| `podcasts.PlayBack` — `app/apps/posts/podcasts/models.py` | user → users.ClerkUser (ForeignKey, SET_NULL, nullable); episode → podcasts.Episode (ForeignKey, CASCADE) | unique_together ('user', 'episode') | no |
| `podcasts.Summary` — `app/apps/posts/podcasts/models.py` | episode → podcasts.Episode (OneToOneField, CASCADE) | unique episode | no |
| `polls.Poll` — `app/apps/posts/polls/models.py` | parent → polls.Poll (ForeignKey, SET_NULL, nullable) | — | yes |
| `polls.Choice` — `app/apps/posts/polls/models.py` | poll → polls.Poll (ForeignKey, CASCADE); votes → users.ClerkUser (ManyToManyField, through=polls.Choice_votes) | — | yes |
| `memberships.AddOn` — `app/apps/memberships/models.py` | — | unique slug | yes |
| `memberships.Entitlement` — `app/apps/memberships/models.py` | user → users.ClerkUser (ForeignKey, CASCADE); content_type → contenttypes.ContentType (ForeignKey, CASCADE); granted_by_subscription → memberships.Subscription (ForeignKey, SET_NULL, nullable); content_object → generic content type/object ID (GenericForeignKey) | unique_together ('user', 'content_type', 'object_id'); index <Index: fields=['user'] name='memberships_user_id_b72bc8_idx'>; index <Index: fields=['content_type', 'object_id'] name='memberships_content_b1ae3d_idx'>; index <Index: fields=['expires_at'] name='memberships_expires_7b61c7_idx'> | yes |
| `memberships.Feature` — `app/apps/memberships/models.py` | — | unique slug | yes |
| `memberships.Plan` — `app/apps/memberships/models.py` | features → memberships.Feature (ManyToManyField, through=memberships.PlanFeature) | — | yes |
| `memberships.PlanFeature` — `app/apps/memberships/models.py` | plan → memberships.Plan (ForeignKey, CASCADE); feature → memberships.Feature (ForeignKey, CASCADE) | unique_together ('plan', 'feature') | no |
| `memberships.Membership` — `app/apps/memberships/models.py` | user → users.ClerkUser (OneToOneField, CASCADE); plan → memberships.Plan (ForeignKey, SET_NULL, nullable) | unique user | yes |
| `memberships.Subscription` — `app/apps/memberships/models.py` | membership → memberships.Membership (ForeignKey, CASCADE) | index <Index: fields=['membership', 'status'] name='memberships_members_d88fa5_idx'> | yes |
| `promotions.PagePromotion` — `app/apps/promotions/models.py` | content_type → contenttypes.ContentType (ForeignKey, CASCADE); content_object → generic content type/object ID (GenericForeignKey) | — | no |
| `promotions.KeywordPromotion` — `app/apps/promotions/models.py` | content_type → contenttypes.ContentType (ForeignKey, CASCADE); content_object → generic content type/object ID (GenericForeignKey) | — | no |
| `promotions.Image` — `app/apps/promotions/models.py` | podcast → podcasts.Podcast (ForeignKey, CASCADE, nullable); keywords → promotions.KeywordPromotion (GenericRelation, DO_NOTHING, nullable); pages → promotions.PagePromotion (GenericRelation, DO_NOTHING, nullable) | index <Index: fields=['banner_status', 'date_created'] name='promotions__banner__cc997a_idx'>; index <Index: fields=['podcast', 'banner_status'] name='promotions__podcast_3ee31a_idx'> | yes |
| `promotions.MultiImage` — `app/apps/promotions/models.py` | images → promotions.Image (ManyToManyField, through=promotions.MultiImage_images); keywords → promotions.KeywordPromotion (GenericRelation, DO_NOTHING, nullable); pages → promotions.PagePromotion (GenericRelation, DO_NOTHING, nullable) | — | yes |
| `promotions.HandPickedPostList` — `app/apps/promotions/models.py` | podcasts → podcasts.Podcast (ManyToManyField, through=promotions.OrderedPodcast); keywords → promotions.KeywordPromotion (GenericRelation, DO_NOTHING, nullable); pages → promotions.PagePromotion (GenericRelation, DO_NOTHING, nullable) | — | yes |
| `promotions.OrderedPodcast` — `app/apps/promotions/models.py` | list → promotions.HandPickedPostList (ForeignKey, CASCADE); podcast → podcasts.Podcast (ForeignKey, CASCADE) | constraint <UniqueConstraint: fields=('list', 'podcast') name='unique_ordered_podcast_in_list'> | yes |
| `promotions.AutomaticPostList` — `app/apps/promotions/models.py` | keywords → promotions.KeywordPromotion (GenericRelation, DO_NOTHING, nullable); pages → promotions.PagePromotion (GenericRelation, DO_NOTHING, nullable) | — | yes |
| `promotions.OrderedPostList` — `app/apps/promotions/models.py` | handpickedpostlist_ptr → promotions.HandPickedPostList (OneToOneField, CASCADE); keywords → promotions.KeywordPromotion (GenericRelation, DO_NOTHING, nullable); pages → promotions.PagePromotion (GenericRelation, DO_NOTHING, nullable) | — | yes |
| `queue.Queue` — `app/apps/queue/models.py` | owner → users.ClerkUser (ForeignKey, CASCADE, nullable) | constraint <CheckConstraint: condition=(OR: ('owner__isnull', False), ('session_key__isnull', False)) name='queue_must_have_owner'>; index <Index: fields=['owner'] name='queue_queue_owner_i_e7a1da_idx'>; index <Index: fields=['last_activity'] name='queue_queue_last_ac_0382e0_idx'>; index <Index: fields=['session_key'] name='queue_queue_session_80aae9_idx'> | yes |
| `queue.QueueItem` — `app/apps/queue/models.py` | queue → queue.Queue (ForeignKey, CASCADE); track → podcasts.Episode (ForeignKey, CASCADE) | unique_together ('queue', 'track') | yes |
| `recommendation.UserCategoryAffinity` — `app/apps/recommendation/models.py` | user → users.ClerkUser (ForeignKey, CASCADE); category → category.Category (ForeignKey, CASCADE) | unique_together ('user', 'category'); index <Index: fields=['user', '-score'] name='recommendat_user_id_158145_idx'>; index <Index: fields=['category'] name='recommendat_categor_bce997_idx'> | yes |
| `leagues.League` — `app/apps/region/leagues/models.py` | region → region.Country (ForeignKey, SET_NULL, nullable) | unique code | yes |
| `leagues.Campaign` — `app/apps/region/leagues/models.py` | — | — | yes |
| `clubs.Team` — `app/apps/region/leagues/clubs/models.py` | league → leagues.League (ForeignKey, SET_NULL, nullable) | unique code | yes |
| `clubs.Stadium` — `app/apps/region/leagues/clubs/models.py` | region → region.Country (ForeignKey, CASCADE); team → clubs.Team (OneToOneField, CASCADE) | unique team | yes |
| `thumbnail.Thumbnail` — `app/apps/thumbnail/models.py` | content_type → contenttypes.ContentType (ForeignKey, CASCADE); content_object → generic content type/object ID (GenericForeignKey) | index <Index: fields=['content_type', 'object_id', 'type'] name='thumbnail_t_content_df4518_idx'> | yes |
| `tactics.Position` — `app/apps/tactics/models.py` | shape → tactics.Shape (ForeignKey, CASCADE) | — | yes |
| `tactics.LineUp` — `app/apps/tactics/models.py` | player → persons.Player (ForeignKey, CASCADE); position → tactics.Position (ForeignKey, CASCADE) | — | yes |
| `tactics.Shape` — `app/apps/tactics/models.py` | style → tactics.FormationStyle (ForeignKey, CASCADE) | — | yes |
| `tactics.FormationStyle` — `app/apps/tactics/models.py` | — | — | yes |
| `tactics.Formation` — `app/apps/tactics/models.py` | shape → tactics.Shape (ForeignKey, CASCADE); lineup → tactics.LineUp (ManyToManyField, through=tactics.Formation_lineup) | — | yes |
| `tactics.TeamLineUp` — `app/apps/tactics/models.py` | team → clubs.Team (ForeignKey, CASCADE); lineup → tactics.Formation (ForeignKey, CASCADE); manager → persons.Staff (ForeignKey, SET_NULL, nullable) | — | yes |
| `tactics.MatchLineUp` — `app/apps/tactics/models.py` | match → match.Match (OneToOneField, CASCADE); home_lineup → tactics.TeamLineUp (ForeignKey, CASCADE); away_lineup → tactics.TeamLineUp (ForeignKey, CASCADE) | unique match | yes |

## Repository migrations

All numbered migrations on disk are listed. Dependencies include package migrations (not counted as repository migrations). This is graph/definition evidence, not deployed apply-state. Existing data migrations require their documented rollback qualifications.

| Migration | Dependencies | Operation counts | Data operations |
|---|---|---|---|
| `app/apps/analytics/migrations/0001_initial.py` | [('contenttypes', '0002_remove_content_type_name'), ('users', '__first__')] | CreateModel ×1 | — |
| `app/apps/analytics/migrations/0002_alter_objectview_object_id.py` | [('analytics', '0001_initial')] | AlterField ×1 | — |
| `app/apps/media/audio/migrations/0001_initial.py` | [] | CreateModel ×1 | — |
| `app/apps/media/audio/migrations/0002_initial.py` | [('audio', '0001_initial'), ('podcasts', '0001_initial')] | AddField ×1, AddIndex ×1, AddConstraint ×2 | — |
| `app/apps/billing/migrations/0001_initial.py` | [('users', '__first__')] | CreateModel ×4 | — |
| `app/apps/billing/migrations/0002_initial.py` | [('billing', '0001_initial'), ('memberships', '0001_initial')] | AddField ×3, AddIndex ×2 | — |
| `app/apps/category/migrations/0001_initial.py` | [] | CreateModel ×1 | — |
| `app/apps/category/migrations/0002_initial.py` | [('category', '0001_initial'), ('memberships', '0001_initial')] | AddField ×1 | — |
| `app/apps/media/chapters/migrations/0001_initial.py` | [] | CreateModel ×1 | — |
| `app/apps/media/chapters/migrations/0002_initial.py` | [('chapters', '0001_initial'), ('podcasts', '0001_initial')] | AddField ×1 | — |
| `app/apps/region/leagues/clubs/migrations/0001_initial.py` | [('leagues', '0001_initial'), ('region', '0001_initial')] | CreateModel ×2 | — |
| `app/apps/region/leagues/clubs/migrations/0002_alter_team_options_team_popularity_alter_team_league.py` | [('clubs', '0001_initial'), ('leagues', '0002_alter_league_options_league_popularity')] | AlterModelOptions ×1, AddField ×1, AlterField ×1 | — |
| `app/apps/comments/migrations/0001_initial.py` | [('contenttypes', '0002_remove_content_type_name'), ('users', '__first__')] | CreateModel ×1 | — |
| `app/apps/comments/migrations/0002_comment_object_id_and_indexes.py` | [('comments', '0001_initial')] | AlterField ×1, AddIndex ×2 | — |
| `app/apps/comments/migrations/0003_rename_comments_ct_oid_ts_idx_comments_co_content_01c7c5_idx_and_more.py` | [('comments', '0002_comment_object_id_and_indexes')] | RenameIndex ×2 | — |
| `app/apps/forum/migrations/0001_initial.py` | [('users', '__first__')] | CreateModel ×2 | — |
| `app/apps/media/images/migrations/0001_initial.py` | [('contenttypes', '0002_remove_content_type_name')] | CreateModel ×1 | — |
| `app/apps/media/images/migrations/0002_image_object_id_metadata_indexes.py` | [('images', '0001_initial')] | AlterField ×2, AddIndex ×1 | — |
| `app/apps/media/images/migrations/0003_alter_image_options_and_more.py` | [('images', '0002_image_object_id_metadata_indexes')] | AlterModelOptions ×1, RenameIndex ×1 | — |
| `app/apps/region/leagues/migrations/0001_initial.py` | [('region', '0001_initial')] | CreateModel ×2 | — |
| `app/apps/region/leagues/migrations/0002_alter_league_options_league_popularity.py` | [('leagues', '0001_initial')] | AlterModelOptions ×1, AddField ×1 | — |
| `app/apps/match/migrations/0001_initial.py` | [('clubs', '0001_initial'), ('persons', '0001_initial'), ('video', '0001_initial')] | CreateModel ×13, AddField ×1 | — |
| `app/apps/match/migrations/0002_initial.py` | [('clubs', '0001_initial'), ('leagues', '0001_initial'), ('match', '0001_initial'), ('persons', '0001_initial'), ('tactics', '0001_initial')] | AddField ×27 | — |
| `app/apps/match/migrations/0003_alter_match_day.py` | [('match', '0002_initial')] | AlterField ×1 | — |
| `app/apps/media/migrations/0001_initial.py` | [('category', '0001_initial'), ('podcasts', '0001_initial'), ('users', '__first__')] | CreateModel ×3, AddField ×1 | — |
| `app/apps/media/migrations/0002_mediaasset_medialocation_mediavariant.py` | [('media', '0001_initial'), ('podcasts', '0001_initial'), ('users', '__first__')] | CreateModel ×3 | — |
| `app/apps/memberships/migrations/0001_initial.py` | [('contenttypes', '0002_remove_content_type_name'), ('users', '__first__')] | CreateModel ×7, AddField ×1, AddIndex ×4, AlterUniqueTogether ×1 | — |
| `app/apps/media/offline/migrations/0001_initial.py` | [('podcasts', '0001_initial'), ('users', '__first__')] | CreateModel ×4, AddIndex ×6, AlterUniqueTogether ×1 | — |
| `app/apps/persons/migrations/0001_initial.py` | [('clubs', '0001_initial'), ('region', '0001_initial')] | CreateModel ×5 | — |
| `app/apps/persons/migrations/0002_contract_rename_name_player_first_name_and_more.py` | [('clubs', '0002_alter_team_options_team_popularity_alter_team_league'), ('persons', '0001_initial'), ('region', '0001_initial')] | CreateModel ×3, RenameField ×2, RemoveField ×4, AddField ×11, AlterField ×1 | — |
| `app/apps/posts/podcasts/migrations/0001_initial.py` | [('category', '0001_initial'), ('clubs', '0001_initial'), ('leagues', '0001_initial'), ('match', '0001_initial'), ('persons', '0001_initial'), ('region', '0001_initial'), ('users', '__first__')] | CreateModel ×4 | — |
| `app/apps/posts/podcasts/migrations/0002_episode_publication_access.py` | [('category', '0002_initial'), ('memberships', '0001_initial'), ('podcasts', '0001_initial')] | AddField ×6, RunPython ×1, AddIndex ×2 | backfill_episode_publication_access / reverse=noop |
| `app/apps/posts/podcasts/migrations/0003_canonical_podcast_seasons.py` | [('podcasts', '0002_episode_publication_access')] | AddField ×11, CreateModel ×1, RunPython ×1, AlterField ×2, AlterModelOptions ×1, AddIndex ×3, AddConstraint ×5 | backfill_canonical_content / reverse=restore_legacy_episode_ownership |
| `app/apps/posts/polls/migrations/0001_initial.py` | [('users', '__first__')] | CreateModel ×2 | — |
| `app/apps/posts/migrations/0001_initial.py` | [('clubs', '0001_initial'), ('contenttypes', '0002_remove_content_type_name'), ('leagues', '0001_initial'), ('match', '0002_initial'), ('persons', '0001_initial'), ('polls', '0001_initial'), ('region', '0001_initial'), ('users', '__first__')] | CreateModel ×2 | — |
| `app/apps/posts/migrations/0002_postreaction_object_id_and_indexes.py` | [('posts', '0001_initial')] | AlterField ×1, AddIndex ×2 | — |
| `app/apps/posts/migrations/0003_rename_posts_react_ct_oid_idx_posts_postr_content_e91cc9_idx_and_more.py` | [('posts', '0002_postreaction_object_id_and_indexes')] | RenameIndex ×2 | — |
| `app/apps/promotions/migrations/0001_initial.py` | [('contenttypes', '0002_remove_content_type_name'), ('podcasts', '0001_initial')] | CreateModel ×8, AddField ×1 | — |
| `app/apps/promotions/migrations/0002_remote_banner_refactor.py` | [('promotions', '0001_initial')] | AlterField ×2, AddField ×19, RunPython ×1, RemoveField ×1, AddIndex ×2, AlterUniqueTogether ×1, AddConstraint ×1 | bootstrap_remote_banner_fields / reverse=noop |
| `app/apps/promotions/migrations/0003_alter_image_options_and_more.py` | [('promotions', '0002_remote_banner_refactor')] | AlterModelOptions ×1, RenameIndex ×2, AlterField ×11 | — |
| `app/apps/queue/migrations/0001_initial.py` | [('podcasts', '0001_initial'), ('users', '__first__')] | CreateModel ×2, AddIndex ×3, AddConstraint ×1, AlterUniqueTogether ×1 | — |
| `app/apps/recommendation/migrations/0001_initial.py` | [('category', '0002_initial'), ('users', '__first__')] | CreateModel ×1 | — |
| `app/apps/region/migrations/0001_initial.py` | [] | CreateModel ×2 | — |
| `app/apps/tactics/migrations/0001_initial.py` | [('clubs', '0001_initial'), ('match', '0001_initial'), ('persons', '0001_initial')] | CreateModel ×7, AddField ×1 | — |
| `app/apps/thumbnail/migrations/0001_initial.py` | [('contenttypes', '0002_remove_content_type_name')] | CreateModel ×1 | — |
| `app/apps/thumbnail/migrations/0002_thumbnail_object_id_and_index.py` | [('thumbnail', '0001_initial')] | AlterField ×1, AddIndex ×1 | — |
| `app/apps/thumbnail/migrations/0003_rename_thumb_ct_oid_type_idx_thumbnail_t_content_df4518_idx.py` | [('thumbnail', '0002_thumbnail_object_id_and_index')] | RenameIndex ×1 | — |
| `app/apps/media/transcription/migrations/0001_initial.py` | [('podcasts', '0001_initial'), ('users', '__first__')] | CreateModel ×3 | — |
| `app/apps/media/video/migrations/0001_initial.py` | [] | CreateModel ×1 | — |

## Resolved public and dashboard routes

Every non-admin leaf URL under test settings is listed below, including DRF format-suffix aliases and API roots. Patterns are Django resolver syntax, not literal client URLs. Test settings disable debug media/static routes; development adds them. Admin is mounted at `/admin/` and its registered repository models are marked above. Permission behavior is defined by each callback and action, not by this list.

| Pattern | Name | Callback / actions |
|---|---|---|
| `/health/live/` | `health-live` | `conf.health.liveness`  |
| `/health/ready/` | `health-ready` | `conf.health.readiness`  |
| `/api/rest/web/apps/media/audio/add/` | `api_apps:media_web_api:add_audio` | `api.rest.web.apps.media.audio.views.MediaAudioAPIView`  |
| `/api/rest/web/apps/media/offline/devices/register/` | `api_apps:media_web_api:media_offline_web_api:register_device` | `api.rest.web.apps.media.offline.views.register_device`  |
| `/api/rest/web/apps/media/offline/packages/request/` | `api_apps:media_web_api:media_offline_web_api:request_offline_package` | `api.rest.web.apps.media.offline.views.request_offline_package`  |
| `/api/rest/web/apps/media/offline/packages/status/<str:task_id>/` | `api_apps:media_web_api:media_offline_web_api:packaging_status` | `api.rest.web.apps.media.offline.views.packaging_status`  |
| `/api/rest/web/apps/media/offline/licenses/<uuid:license_id>/revoke/` | `api_apps:media_web_api:media_offline_web_api:revoke_offline_license` | `api.rest.web.apps.media.offline.views.revoke_license`  |
| `/api/rest/web/apps/media/streaming/episodes/<uuid:episode_id>/stream/` | `api_apps:media_web_api:media_streaming_web_api:stream_episode_progressive` | `api.rest.web.apps.media.streaming.views.stream_episode_progressive`  |
| `/api/rest/web/apps/podcast/auto/` | `api_apps:podcast_web_api:auto` | `api.rest.web.apps.podcasts.views.AutomaticPromotionAPIView`  |
| `/api/rest/web/apps/podcast/handpicked/` | `api_apps:podcast_web_api:handpicked` | `api.rest.web.apps.podcasts.views.HandpickedPromotionsAPIView`  |
| `/api/rest/web/apps/podcast/promotions/` | `api_apps:podcast_web_api:promotions` | `api.rest.web.apps.podcasts.views.PromotionsAPIView`  |
| `/api/rest/web/apps/podcast/trending/` | `api_apps:podcast_web_api:trending-podcast` | `api.rest.web.apps.podcasts.views.TrendingPodcastAPIView`  |
| `/api/rest/web/apps/podcast/recently-viewed/` | `api_apps:podcast_web_api:recently-viewed` | `api.rest.web.apps.podcasts.views.RecentlyViewedPodcastAPIView`  |
| `/api/rest/web/apps/podcast/recently-played/` | `api_apps:podcast_web_api:recently-played` | `api.rest.web.apps.podcasts.views.PlayBackListApiView`  |
| `/api/rest/web/apps/podcast/resume-playback/` | `api_apps:podcast_web_api:resume-playback` | `api.rest.web.apps.podcasts.views.PlaybackUncompletedListAPIView`  |
| `/api/rest/web/apps/podcast/<slug:slug>/` | `api_apps:podcast_web_api:podcast-detail` | `api.rest.web.apps.podcasts.views.PodcastDetailAPIView`  |
| `/api/rest/web/apps/podcast/<slug:slug>/episodes/` | `api_apps:podcast_web_api:episodes-list` | `api.rest.web.apps.podcasts.views.EpisodeListAPIView`  |
| `/api/rest/web/apps/podcast/episode/<slug:slug>/` | `api_apps:podcast_web_api:episode-detail` | `api.rest.web.apps.podcasts.views.EpisodeDetailAPIView`  |
| `/api/rest/web/apps/podcast/episode/<slug:slug>/update-playback` | `api_apps:podcast_web_api:episode-update-playback` | `api.rest.web.apps.podcasts.views.PlaybackUpdateAPIView`  |
| `/api/rest/web/apps/profile/subscribe/` | `api_apps:profile_web_api:user-subscription` | `api.rest.web.apps.profile.views.UserSubscriptionAPIView`  |
| `/api/rest/web/apps/profile/subscriptions/podcast/` | `api_apps:profile_web_api:subscriptions` | `api.rest.web.apps.profile.views.SubscribedListPodcastAPIView`  |
| `/api/rest/web/apps/profile/playlists/featured/` | `api_apps:profile_web_api:featured-playlist` | `api.rest.web.apps.profile.views.FeaturedPlayListAPIView`  |
| `/api/rest/web/apps/profile/playlists/` | `api_apps:profile_web_api:add-to-playlist` | `api.rest.web.apps.profile.views.PlaylistUserViewSet` {'get': 'list', 'post': 'create'} |
| `/api/rest/web/apps/profile/playlists/<int:pk>/` | `api_apps:profile_web_api:playlist-detail` | `api.rest.web.apps.profile.views.PlaylistUserViewSet` {'get': 'view_item', 'put': 'update', 'delete': 'destroy', 'patch': 'partial_update'} |
| `/api/rest/web/apps/profile/playlist/<int:pk>/add` | `api_apps:profile_web_api:add-to-playlist` | `api.rest.web.apps.profile.views.PlaylistUserViewSet` {'post': 'add_item'} |
| `/api/rest/web/apps/profile/playlist/<int:pk>/remove` | `api_apps:profile_web_api:remove-from-playlist` | `api.rest.web.apps.profile.views.PlaylistUserViewSet` {'post': 'remove_item'} |
| `/api/rest/web/apps/profile/playlist/<int:pk>/reorder` | `api_apps:profile_web_api:reorder-playlist` | `api.rest.web.apps.profile.views.PlaylistUserViewSet` {'post': 'reorder'} |
| `/api/rest/web/apps/comment/create/` | `api_apps:comment_web_api:create` | `api.rest.web.apps.comments.views.CommentCreateAPIView`  |
| `/api/rest/web/apps/queue/` | `api_apps:queue_web_api:queue` | `api.rest.web.apps.queue.views.QueueViewSet` {'get': 'list'} |
| `/api/rest/web/apps/queue/add/` | `api_apps:queue_web_api:queue-add` | `api.rest.web.apps.queue.views.QueueViewSet` {'post': 'add'} |
| `/api/rest/web/apps/queue/clear/` | `api_apps:queue_web_api:queue-clear` | `api.rest.web.apps.queue.views.QueueViewSet` {'put': 'clear'} |
| `/api/rest/web/apps/queue/<uuid:episode_id>/remove/` | `api_apps:queue_web_api:queue-item-remove` | `api.rest.web.apps.queue.views.QueueViewSet` {'delete': 'remove'} |
| `/api/rest/web/explore/` | `explore` | `api.rest.web.views.ExploreAPIView`  |
| `/api/rest/dashboard/apps/matches/^$` | `match-list` | `api.rest.dashboard.apps.match.views.MatchViewSet` {'get': 'list', 'post': 'create'} |
| `/api/rest/dashboard/apps/matches/^\.(?P<format>[a-z0-9]+)/?$` | `match-list` | `api.rest.dashboard.apps.match.views.MatchViewSet` {'get': 'list', 'post': 'create'} |
| `/api/rest/dashboard/apps/matches/^(?P<pk>[^/.]+)/$` | `match-detail` | `api.rest.dashboard.apps.match.views.MatchViewSet` {'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'} |
| `/api/rest/dashboard/apps/matches/^(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$` | `match-detail` | `api.rest.dashboard.apps.match.views.MatchViewSet` {'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'} |
| `/api/rest/dashboard/apps/matches/^(?P<pk>[^/.]+)/live/booking/$` | `match-create-booking` | `api.rest.dashboard.apps.match.views.MatchViewSet` {'post': 'create_booking'} |
| `/api/rest/dashboard/apps/matches/^(?P<pk>[^/.]+)/live/booking\.(?P<format>[a-z0-9]+)/?$` | `match-create-booking` | `api.rest.dashboard.apps.match.views.MatchViewSet` {'post': 'create_booking'} |
| `/api/rest/dashboard/apps/matches/^(?P<pk>[^/.]+)/live/foul/$` | `match-create-foul` | `api.rest.dashboard.apps.match.views.MatchViewSet` {'post': 'create_foul'} |
| `/api/rest/dashboard/apps/matches/^(?P<pk>[^/.]+)/live/foul\.(?P<format>[a-z0-9]+)/?$` | `match-create-foul` | `api.rest.dashboard.apps.match.views.MatchViewSet` {'post': 'create_foul'} |
| `/api/rest/dashboard/apps/matches/^(?P<pk>[^/.]+)/live/goal/$` | `match-create-goal` | `api.rest.dashboard.apps.match.views.MatchViewSet` {'post': 'create_goal'} |
| `/api/rest/dashboard/apps/matches/^(?P<pk>[^/.]+)/live/goal\.(?P<format>[a-z0-9]+)/?$` | `match-create-goal` | `api.rest.dashboard.apps.match.views.MatchViewSet` {'post': 'create_goal'} |
| `/api/rest/dashboard/apps/matches/^(?P<pk>[^/.]+)/live/set-piece/$` | `match-create-set-piece` | `api.rest.dashboard.apps.match.views.MatchViewSet` {'post': 'create_set_piece'} |
| `/api/rest/dashboard/apps/matches/^(?P<pk>[^/.]+)/live/set-piece\.(?P<format>[a-z0-9]+)/?$` | `match-create-set-piece` | `api.rest.dashboard.apps.match.views.MatchViewSet` {'post': 'create_set_piece'} |
| `/api/rest/dashboard/apps/matches/^(?P<pk>[^/.]+)/live/shot/$` | `match-create-shot` | `api.rest.dashboard.apps.match.views.MatchViewSet` {'post': 'create_shot'} |
| `/api/rest/dashboard/apps/matches/^(?P<pk>[^/.]+)/live/shot\.(?P<format>[a-z0-9]+)/?$` | `match-create-shot` | `api.rest.dashboard.apps.match.views.MatchViewSet` {'post': 'create_shot'} |
| `/api/rest/dashboard/apps/matches/^(?P<pk>[^/.]+)/live/substitution/$` | `match-create-substitution` | `api.rest.dashboard.apps.match.views.MatchViewSet` {'post': 'create_substitution'} |
| `/api/rest/dashboard/apps/matches/^(?P<pk>[^/.]+)/live/substitution\.(?P<format>[a-z0-9]+)/?$` | `match-create-substitution` | `api.rest.dashboard.apps.match.views.MatchViewSet` {'post': 'create_substitution'} |
| `/api/rest/dashboard/apps/matches/^(?P<pk>[^/.]+)/lineups/$` | `match-match-lineups` | `api.rest.dashboard.apps.match.views.MatchViewSet` {'post': 'match_lineups'} |
| `/api/rest/dashboard/apps/matches/^(?P<pk>[^/.]+)/lineups\.(?P<format>[a-z0-9]+)/?$` | `match-match-lineups` | `api.rest.dashboard.apps.match.views.MatchViewSet` {'post': 'match_lineups'} |
| `/api/rest/dashboard/apps/matches/^(?P<pk>[^/.]+)/timeline/$` | `match-timeline` | `api.rest.dashboard.apps.match.views.MatchViewSet` {'get': 'timeline'} |
| `/api/rest/dashboard/apps/matches/^(?P<pk>[^/.]+)/timeline\.(?P<format>[a-z0-9]+)/?$` | `match-timeline` | `api.rest.dashboard.apps.match.views.MatchViewSet` {'get': 'timeline'} |
| `/api/rest/dashboard/apps/matches/^(?P<pk>[^/.]+)/lineups/$` | `match-update-lineups` | `api.rest.dashboard.apps.match.views.MatchViewSet` {'patch': 'update_lineups'} |
| `/api/rest/dashboard/apps/matches/^(?P<pk>[^/.]+)/lineups\.(?P<format>[a-z0-9]+)/?$` | `match-update-lineups` | `api.rest.dashboard.apps.match.views.MatchViewSet` {'patch': 'update_lineups'} |
| `/api/rest/dashboard/apps/matches/` | `api-root` | `rest_framework.routers.APIRootView`  |
| `/api/rest/dashboard/apps/matches/<drf_format_suffix:format>` | `api-root` | `rest_framework.routers.APIRootView`  |
| `/api/rest/dashboard/apps/memberships/^features/$` | `memberships:feature-list` | `api.rest.dashboard.apps.memberships.views.FeatureViewSet` {'get': 'list', 'post': 'create'} |
| `/api/rest/dashboard/apps/memberships/^features\.(?P<format>[a-z0-9]+)/?$` | `memberships:feature-list` | `api.rest.dashboard.apps.memberships.views.FeatureViewSet` {'get': 'list', 'post': 'create'} |
| `/api/rest/dashboard/apps/memberships/^features/(?P<pk>[^/.]+)/$` | `memberships:feature-detail` | `api.rest.dashboard.apps.memberships.views.FeatureViewSet` {'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'} |
| `/api/rest/dashboard/apps/memberships/^features/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$` | `memberships:feature-detail` | `api.rest.dashboard.apps.memberships.views.FeatureViewSet` {'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'} |
| `/api/rest/dashboard/apps/memberships/^plans/$` | `memberships:plan-list` | `api.rest.dashboard.apps.memberships.views.PlanViewSet` {'get': 'list', 'post': 'create'} |
| `/api/rest/dashboard/apps/memberships/^plans\.(?P<format>[a-z0-9]+)/?$` | `memberships:plan-list` | `api.rest.dashboard.apps.memberships.views.PlanViewSet` {'get': 'list', 'post': 'create'} |
| `/api/rest/dashboard/apps/memberships/^plans/(?P<pk>[^/.]+)/$` | `memberships:plan-detail` | `api.rest.dashboard.apps.memberships.views.PlanViewSet` {'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'} |
| `/api/rest/dashboard/apps/memberships/^plans/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$` | `memberships:plan-detail` | `api.rest.dashboard.apps.memberships.views.PlanViewSet` {'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'} |
| `/api/rest/dashboard/apps/memberships/^plans/(?P<pk>[^/.]+)/add_feature/$` | `memberships:plan-add-feature` | `api.rest.dashboard.apps.memberships.views.PlanViewSet` {'post': 'add_feature'} |
| `/api/rest/dashboard/apps/memberships/^plans/(?P<pk>[^/.]+)/add_feature\.(?P<format>[a-z0-9]+)/?$` | `memberships:plan-add-feature` | `api.rest.dashboard.apps.memberships.views.PlanViewSet` {'post': 'add_feature'} |
| `/api/rest/dashboard/apps/memberships/^plan-features/$` | `memberships:planfeature-list` | `api.rest.dashboard.apps.memberships.views.PlanFeatureViewSet` {'get': 'list', 'post': 'create'} |
| `/api/rest/dashboard/apps/memberships/^plan-features\.(?P<format>[a-z0-9]+)/?$` | `memberships:planfeature-list` | `api.rest.dashboard.apps.memberships.views.PlanFeatureViewSet` {'get': 'list', 'post': 'create'} |
| `/api/rest/dashboard/apps/memberships/^plan-features/(?P<pk>[^/.]+)/$` | `memberships:planfeature-detail` | `api.rest.dashboard.apps.memberships.views.PlanFeatureViewSet` {'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'} |
| `/api/rest/dashboard/apps/memberships/^plan-features/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$` | `memberships:planfeature-detail` | `api.rest.dashboard.apps.memberships.views.PlanFeatureViewSet` {'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'} |
| `/api/rest/dashboard/apps/memberships/^entitlements/$` | `memberships:entitlement-list` | `api.rest.dashboard.apps.memberships.views.EntitlementViewSet` {'get': 'list', 'post': 'create'} |
| `/api/rest/dashboard/apps/memberships/^entitlements\.(?P<format>[a-z0-9]+)/?$` | `memberships:entitlement-list` | `api.rest.dashboard.apps.memberships.views.EntitlementViewSet` {'get': 'list', 'post': 'create'} |
| `/api/rest/dashboard/apps/memberships/^entitlements/(?P<pk>[^/.]+)/$` | `memberships:entitlement-detail` | `api.rest.dashboard.apps.memberships.views.EntitlementViewSet` {'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'} |
| `/api/rest/dashboard/apps/memberships/^entitlements/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$` | `memberships:entitlement-detail` | `api.rest.dashboard.apps.memberships.views.EntitlementViewSet` {'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'} |
| `/api/rest/dashboard/apps/memberships/^subscriptions/$` | `memberships:subscription-list` | `api.rest.dashboard.apps.memberships.views.SubscriptionViewSet` {'get': 'list', 'post': 'create'} |
| `/api/rest/dashboard/apps/memberships/^subscriptions\.(?P<format>[a-z0-9]+)/?$` | `memberships:subscription-list` | `api.rest.dashboard.apps.memberships.views.SubscriptionViewSet` {'get': 'list', 'post': 'create'} |
| `/api/rest/dashboard/apps/memberships/^subscriptions/(?P<pk>[^/.]+)/$` | `memberships:subscription-detail` | `api.rest.dashboard.apps.memberships.views.SubscriptionViewSet` {'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'} |
| `/api/rest/dashboard/apps/memberships/^subscriptions/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$` | `memberships:subscription-detail` | `api.rest.dashboard.apps.memberships.views.SubscriptionViewSet` {'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'} |
| `/api/rest/dashboard/apps/memberships/^$` | `memberships:membership-list` | `api.rest.dashboard.apps.memberships.views.MembershipViewSet` {'get': 'list', 'post': 'create'} |
| `/api/rest/dashboard/apps/memberships/^\.(?P<format>[a-z0-9]+)/?$` | `memberships:membership-list` | `api.rest.dashboard.apps.memberships.views.MembershipViewSet` {'get': 'list', 'post': 'create'} |
| `/api/rest/dashboard/apps/memberships/^(?P<pk>[^/.]+)/$` | `memberships:membership-detail` | `api.rest.dashboard.apps.memberships.views.MembershipViewSet` {'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'} |
| `/api/rest/dashboard/apps/memberships/^(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$` | `memberships:membership-detail` | `api.rest.dashboard.apps.memberships.views.MembershipViewSet` {'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'} |
| `/api/rest/dashboard/apps/memberships/` | `memberships:api-root` | `rest_framework.routers.APIRootView`  |
| `/api/rest/dashboard/apps/memberships/<drf_format_suffix:format>` | `memberships:api-root` | `rest_framework.routers.APIRootView`  |
| `/api/rest/dashboard/apps/podcasts/^seasons/$` | `season-list` | `api.rest.dashboard.apps.podcasts.views.SeasonViewSet` {'get': 'list', 'post': 'create'} |
| `/api/rest/dashboard/apps/podcasts/^seasons\.(?P<format>[a-z0-9]+)/?$` | `season-list` | `api.rest.dashboard.apps.podcasts.views.SeasonViewSet` {'get': 'list', 'post': 'create'} |
| `/api/rest/dashboard/apps/podcasts/^seasons/(?P<pk>[^/.]+)/$` | `season-detail` | `api.rest.dashboard.apps.podcasts.views.SeasonViewSet` {'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'} |
| `/api/rest/dashboard/apps/podcasts/^seasons/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$` | `season-detail` | `api.rest.dashboard.apps.podcasts.views.SeasonViewSet` {'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'} |
| `/api/rest/dashboard/apps/podcasts/^episodes/$` | `episode-list` | `api.rest.dashboard.apps.podcasts.views.EpisodeViewSet` {'get': 'list', 'post': 'create'} |
| `/api/rest/dashboard/apps/podcasts/^episodes\.(?P<format>[a-z0-9]+)/?$` | `episode-list` | `api.rest.dashboard.apps.podcasts.views.EpisodeViewSet` {'get': 'list', 'post': 'create'} |
| `/api/rest/dashboard/apps/podcasts/^episodes/(?P<pk>[^/.]+)/$` | `episode-detail` | `api.rest.dashboard.apps.podcasts.views.EpisodeViewSet` {'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'} |
| `/api/rest/dashboard/apps/podcasts/^episodes/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$` | `episode-detail` | `api.rest.dashboard.apps.podcasts.views.EpisodeViewSet` {'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'} |
| `/api/rest/dashboard/apps/podcasts/^episodes/(?P<pk>[^/.]+)/audios/$` | `episode-audios` | `api.rest.dashboard.apps.podcasts.views.EpisodeViewSet` {'get': 'audios'} |
| `/api/rest/dashboard/apps/podcasts/^episodes/(?P<pk>[^/.]+)/audios\.(?P<format>[a-z0-9]+)/?$` | `episode-audios` | `api.rest.dashboard.apps.podcasts.views.EpisodeViewSet` {'get': 'audios'} |
| `/api/rest/dashboard/apps/podcasts/^episodes/(?P<pk>[^/.]+)/audio/(?P<audio_id>[^/.]+)/$` | `episode-delete-audio` | `api.rest.dashboard.apps.podcasts.views.EpisodeViewSet` {'delete': 'delete_audio'} |
| `/api/rest/dashboard/apps/podcasts/^episodes/(?P<pk>[^/.]+)/audio/(?P<audio_id>[^/.]+)\.(?P<format>[a-z0-9]+)/?$` | `episode-delete-audio` | `api.rest.dashboard.apps.podcasts.views.EpisodeViewSet` {'delete': 'delete_audio'} |
| `/api/rest/dashboard/apps/podcasts/^episodes/(?P<pk>[^/.]+)/images/(?P<image_id>[^/.]+)/$` | `episode-delete-image` | `api.rest.dashboard.apps.podcasts.views.EpisodeViewSet` {'delete': 'delete_image'} |
| `/api/rest/dashboard/apps/podcasts/^episodes/(?P<pk>[^/.]+)/images/(?P<image_id>[^/.]+)\.(?P<format>[a-z0-9]+)/?$` | `episode-delete-image` | `api.rest.dashboard.apps.podcasts.views.EpisodeViewSet` {'delete': 'delete_image'} |
| `/api/rest/dashboard/apps/podcasts/^episodes/(?P<pk>[^/.]+)/audio/(?P<audio_id>[^/.]+)/$` | `episode-update-audio` | `api.rest.dashboard.apps.podcasts.views.EpisodeViewSet` {'patch': 'update_audio'} |
| `/api/rest/dashboard/apps/podcasts/^episodes/(?P<pk>[^/.]+)/audio/(?P<audio_id>[^/.]+)\.(?P<format>[a-z0-9]+)/?$` | `episode-update-audio` | `api.rest.dashboard.apps.podcasts.views.EpisodeViewSet` {'patch': 'update_audio'} |
| `/api/rest/dashboard/apps/podcasts/^episodes/(?P<pk>[^/.]+)/upload_audio/$` | `episode-upload-audio` | `api.rest.dashboard.apps.podcasts.views.EpisodeViewSet` {'post': 'upload_audio'} |
| `/api/rest/dashboard/apps/podcasts/^episodes/(?P<pk>[^/.]+)/upload_audio\.(?P<format>[a-z0-9]+)/?$` | `episode-upload-audio` | `api.rest.dashboard.apps.podcasts.views.EpisodeViewSet` {'post': 'upload_audio'} |
| `/api/rest/dashboard/apps/podcasts/^episodes/(?P<pk>[^/.]+)/images/$` | `episode-upload-image` | `api.rest.dashboard.apps.podcasts.views.EpisodeViewSet` {'post': 'upload_image'} |
| `/api/rest/dashboard/apps/podcasts/^episodes/(?P<pk>[^/.]+)/images\.(?P<format>[a-z0-9]+)/?$` | `episode-upload-image` | `api.rest.dashboard.apps.podcasts.views.EpisodeViewSet` {'post': 'upload_image'} |
| `/api/rest/dashboard/apps/podcasts/^$` | `podcasts-list` | `api.rest.dashboard.apps.podcasts.views.PodcastViewSet` {'get': 'list', 'post': 'create'} |
| `/api/rest/dashboard/apps/podcasts/^\.(?P<format>[a-z0-9]+)/?$` | `podcasts-list` | `api.rest.dashboard.apps.podcasts.views.PodcastViewSet` {'get': 'list', 'post': 'create'} |
| `/api/rest/dashboard/apps/podcasts/^(?P<pk>[^/.]+)/$` | `podcasts-detail` | `api.rest.dashboard.apps.podcasts.views.PodcastViewSet` {'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'} |
| `/api/rest/dashboard/apps/podcasts/^(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$` | `podcasts-detail` | `api.rest.dashboard.apps.podcasts.views.PodcastViewSet` {'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'} |
| `/api/rest/dashboard/apps/podcasts/^(?P<pk>[^/.]+)/images/(?P<image_id>[^/.]+)/$` | `podcasts-delete-image` | `api.rest.dashboard.apps.podcasts.views.PodcastViewSet` {'delete': 'delete_image'} |
| `/api/rest/dashboard/apps/podcasts/^(?P<pk>[^/.]+)/images/(?P<image_id>[^/.]+)\.(?P<format>[a-z0-9]+)/?$` | `podcasts-delete-image` | `api.rest.dashboard.apps.podcasts.views.PodcastViewSet` {'delete': 'delete_image'} |
| `/api/rest/dashboard/apps/podcasts/^(?P<pk>[^/.]+)/episodes/$` | `podcasts-episodes` | `api.rest.dashboard.apps.podcasts.views.PodcastViewSet` {'get': 'episodes'} |
| `/api/rest/dashboard/apps/podcasts/^(?P<pk>[^/.]+)/episodes\.(?P<format>[a-z0-9]+)/?$` | `podcasts-episodes` | `api.rest.dashboard.apps.podcasts.views.PodcastViewSet` {'get': 'episodes'} |
| `/api/rest/dashboard/apps/podcasts/^(?P<pk>[^/.]+)/seasons/$` | `podcasts-seasons` | `api.rest.dashboard.apps.podcasts.views.PodcastViewSet` {'get': 'seasons'} |
| `/api/rest/dashboard/apps/podcasts/^(?P<pk>[^/.]+)/seasons\.(?P<format>[a-z0-9]+)/?$` | `podcasts-seasons` | `api.rest.dashboard.apps.podcasts.views.PodcastViewSet` {'get': 'seasons'} |
| `/api/rest/dashboard/apps/podcasts/^(?P<pk>[^/.]+)/images/$` | `podcasts-upload-image` | `api.rest.dashboard.apps.podcasts.views.PodcastViewSet` {'post': 'upload_image'} |
| `/api/rest/dashboard/apps/podcasts/^(?P<pk>[^/.]+)/images\.(?P<format>[a-z0-9]+)/?$` | `podcasts-upload-image` | `api.rest.dashboard.apps.podcasts.views.PodcastViewSet` {'post': 'upload_image'} |
| `/api/rest/dashboard/apps/podcasts/` | `api-root` | `rest_framework.routers.APIRootView`  |
| `/api/rest/dashboard/apps/podcasts/<drf_format_suffix:format>` | `api-root` | `rest_framework.routers.APIRootView`  |
| `/api/rest/dashboard/apps/promotions/^images/$` | `promotions_dashboard_api:promotion-image-list` | `api.rest.dashboard.apps.promotions.views.ImagePromotionViewSet` {'get': 'list', 'post': 'create'} |
| `/api/rest/dashboard/apps/promotions/^images\.(?P<format>[a-z0-9]+)/?$` | `promotions_dashboard_api:promotion-image-list` | `api.rest.dashboard.apps.promotions.views.ImagePromotionViewSet` {'get': 'list', 'post': 'create'} |
| `/api/rest/dashboard/apps/promotions/^images/(?P<pk>[^/.]+)/$` | `promotions_dashboard_api:promotion-image-detail` | `api.rest.dashboard.apps.promotions.views.ImagePromotionViewSet` {'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'} |
| `/api/rest/dashboard/apps/promotions/^images/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$` | `promotions_dashboard_api:promotion-image-detail` | `api.rest.dashboard.apps.promotions.views.ImagePromotionViewSet` {'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'} |
| `/api/rest/dashboard/apps/promotions/^images/(?P<pk>[^/.]+)/refresh-status/$` | `promotions_dashboard_api:promotion-image-refresh-status` | `api.rest.dashboard.apps.promotions.views.ImagePromotionViewSet` {'post': 'refresh_status'} |
| `/api/rest/dashboard/apps/promotions/^images/(?P<pk>[^/.]+)/refresh-status\.(?P<format>[a-z0-9]+)/?$` | `promotions_dashboard_api:promotion-image-refresh-status` | `api.rest.dashboard.apps.promotions.views.ImagePromotionViewSet` {'post': 'refresh_status'} |
| `/api/rest/dashboard/apps/promotions/` | `promotions_dashboard_api:api-root` | `rest_framework.routers.APIRootView`  |
| `/api/rest/dashboard/apps/promotions/<drf_format_suffix:format>` | `promotions_dashboard_api:api-root` | `rest_framework.routers.APIRootView`  |
| `/api/rest/dashboard/apps/promotions/callbacks/giffy/` | `promotions_dashboard_api:giffy-callback` | `api.rest.dashboard.apps.promotions.views.GiffyCallbackAPIView`  |
| `/api/rest/dashboard/apps/persons/^players/$` | `player-list` | `api.rest.dashboard.apps.persons.views.PlayerViewSet` {'get': 'list', 'post': 'create'} |
| `/api/rest/dashboard/apps/persons/^players\.(?P<format>[a-z0-9]+)/?$` | `player-list` | `api.rest.dashboard.apps.persons.views.PlayerViewSet` {'get': 'list', 'post': 'create'} |
| `/api/rest/dashboard/apps/persons/^players/injury-types/$` | `player-injury-types` | `api.rest.dashboard.apps.persons.views.PlayerViewSet` {'get': 'injury_types', 'post': 'injury_types'} |
| `/api/rest/dashboard/apps/persons/^players/injury-types\.(?P<format>[a-z0-9]+)/?$` | `player-injury-types` | `api.rest.dashboard.apps.persons.views.PlayerViewSet` {'get': 'injury_types', 'post': 'injury_types'} |
| `/api/rest/dashboard/apps/persons/^players/(?P<pk>[^/.]+)/$` | `player-detail` | `api.rest.dashboard.apps.persons.views.PlayerViewSet` {'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'} |
| `/api/rest/dashboard/apps/persons/^players/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$` | `player-detail` | `api.rest.dashboard.apps.persons.views.PlayerViewSet` {'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'} |
| `/api/rest/dashboard/apps/persons/^players/(?P<pk>[^/.]+)/transfer/(?P<transfer_pk>[^/.]+)/$` | `player-contract` | `api.rest.dashboard.apps.persons.views.PlayerViewSet` {'get': 'contract', 'delete': 'contract'} |
| `/api/rest/dashboard/apps/persons/^players/(?P<pk>[^/.]+)/transfer/(?P<transfer_pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$` | `player-contract` | `api.rest.dashboard.apps.persons.views.PlayerViewSet` {'get': 'contract', 'delete': 'contract'} |
| `/api/rest/dashboard/apps/persons/^players/(?P<pk>[^/.]+)/fitness/$` | `player-fitness` | `api.rest.dashboard.apps.persons.views.PlayerViewSet` {'get': 'fitness', 'post': 'fitness', 'put': 'fitness', 'patch': 'fitness'} |
| `/api/rest/dashboard/apps/persons/^players/(?P<pk>[^/.]+)/fitness\.(?P<format>[a-z0-9]+)/?$` | `player-fitness` | `api.rest.dashboard.apps.persons.views.PlayerViewSet` {'get': 'fitness', 'post': 'fitness', 'put': 'fitness', 'patch': 'fitness'} |
| `/api/rest/dashboard/apps/persons/^players/(?P<pk>[^/.]+)/injuries/$` | `player-injuries` | `api.rest.dashboard.apps.persons.views.PlayerViewSet` {'get': 'injuries', 'post': 'injuries'} |
| `/api/rest/dashboard/apps/persons/^players/(?P<pk>[^/.]+)/injuries\.(?P<format>[a-z0-9]+)/?$` | `player-injuries` | `api.rest.dashboard.apps.persons.views.PlayerViewSet` {'get': 'injuries', 'post': 'injuries'} |
| `/api/rest/dashboard/apps/persons/^players/(?P<pk>[^/.]+)/injuries/(?P<injury_pk>[^/.]+)/$` | `player-injury-detail` | `api.rest.dashboard.apps.persons.views.PlayerViewSet` {'get': 'injury_detail', 'put': 'injury_detail', 'patch': 'injury_detail', 'delete': 'injury_detail'} |
| `/api/rest/dashboard/apps/persons/^players/(?P<pk>[^/.]+)/injuries/(?P<injury_pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$` | `player-injury-detail` | `api.rest.dashboard.apps.persons.views.PlayerViewSet` {'get': 'injury_detail', 'put': 'injury_detail', 'patch': 'injury_detail', 'delete': 'injury_detail'} |
| `/api/rest/dashboard/apps/persons/^players/(?P<pk>[^/.]+)/transfers/$` | `player-transfers` | `api.rest.dashboard.apps.persons.views.PlayerViewSet` {'get': 'transfers', 'post': 'transfers'} |
| `/api/rest/dashboard/apps/persons/^players/(?P<pk>[^/.]+)/transfers\.(?P<format>[a-z0-9]+)/?$` | `player-transfers` | `api.rest.dashboard.apps.persons.views.PlayerViewSet` {'get': 'transfers', 'post': 'transfers'} |
| `/api/rest/dashboard/apps/persons/^staff/$` | `staff-list` | `api.rest.dashboard.apps.persons.views.StaffViewSet` {'get': 'list', 'post': 'create'} |
| `/api/rest/dashboard/apps/persons/^staff\.(?P<format>[a-z0-9]+)/?$` | `staff-list` | `api.rest.dashboard.apps.persons.views.StaffViewSet` {'get': 'list', 'post': 'create'} |
| `/api/rest/dashboard/apps/persons/^staff/(?P<pk>[^/.]+)/$` | `staff-detail` | `api.rest.dashboard.apps.persons.views.StaffViewSet` {'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'} |
| `/api/rest/dashboard/apps/persons/^staff/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$` | `staff-detail` | `api.rest.dashboard.apps.persons.views.StaffViewSet` {'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'} |
| `/api/rest/dashboard/apps/persons/` | `api-root` | `rest_framework.routers.APIRootView`  |
| `/api/rest/dashboard/apps/persons/<drf_format_suffix:format>` | `api-root` | `rest_framework.routers.APIRootView`  |
| `/api/rest/dashboard/apps/regions/countries/` | `—` | `api.rest.dashboard.apps.region.views.CountryListAPIView`  |
| `/api/rest/dashboard/apps/regions/leagues/` | `—` | `api.rest.dashboard.apps.region.views.LeagueListAPIView`  |
| `/api/rest/dashboard/apps/regions/teams/` | `—` | `api.rest.dashboard.apps.region.views.TeamListAPIView`  |
| `/api/rest/dashboard/apps/regions/^$` | `region-list` | `api.rest.dashboard.apps.region.views.RegionViewSet` {'get': 'list', 'post': 'create'} |
| `/api/rest/dashboard/apps/regions/^\.(?P<format>[a-z0-9]+)/?$` | `region-list` | `api.rest.dashboard.apps.region.views.RegionViewSet` {'get': 'list', 'post': 'create'} |
| `/api/rest/dashboard/apps/regions/^(?P<pk>[^/.]+)/$` | `region-detail` | `api.rest.dashboard.apps.region.views.RegionViewSet` {'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'} |
| `/api/rest/dashboard/apps/regions/^(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$` | `region-detail` | `api.rest.dashboard.apps.region.views.RegionViewSet` {'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'} |
| `/api/rest/dashboard/apps/regions/^(?P<pk>[^/.]+)/countries/$` | `region-countries` | `api.rest.dashboard.apps.region.views.RegionViewSet` {'get': 'countries', 'post': 'countries'} |
| `/api/rest/dashboard/apps/regions/^(?P<pk>[^/.]+)/countries\.(?P<format>[a-z0-9]+)/?$` | `region-countries` | `api.rest.dashboard.apps.region.views.RegionViewSet` {'get': 'countries', 'post': 'countries'} |
| `/api/rest/dashboard/apps/regions/^(?P<pk>[^/.]+)/countries/(?P<country_id>[^/.]+)/$` | `region-country-detail` | `api.rest.dashboard.apps.region.views.RegionViewSet` {'get': 'country_detail', 'put': 'country_detail', 'patch': 'country_detail', 'delete': 'country_detail'} |
| `/api/rest/dashboard/apps/regions/^(?P<pk>[^/.]+)/countries/(?P<country_id>[^/.]+)\.(?P<format>[a-z0-9]+)/?$` | `region-country-detail` | `api.rest.dashboard.apps.region.views.RegionViewSet` {'get': 'country_detail', 'put': 'country_detail', 'patch': 'country_detail', 'delete': 'country_detail'} |
| `/api/rest/dashboard/apps/regions/^(?P<pk>[^/.]+)/countries/(?P<country_id>[^/.]+)/leagues/(?P<league_id>[^/.]+)/$` | `region-league-detail` | `api.rest.dashboard.apps.region.views.RegionViewSet` {'get': 'league_detail', 'put': 'league_detail', 'patch': 'league_detail', 'delete': 'league_detail'} |
| `/api/rest/dashboard/apps/regions/^(?P<pk>[^/.]+)/countries/(?P<country_id>[^/.]+)/leagues/(?P<league_id>[^/.]+)\.(?P<format>[a-z0-9]+)/?$` | `region-league-detail` | `api.rest.dashboard.apps.region.views.RegionViewSet` {'get': 'league_detail', 'put': 'league_detail', 'patch': 'league_detail', 'delete': 'league_detail'} |
| `/api/rest/dashboard/apps/regions/^(?P<pk>[^/.]+)/countries/(?P<country_id>[^/.]+)/leagues/$` | `region-leagues` | `api.rest.dashboard.apps.region.views.RegionViewSet` {'get': 'leagues', 'post': 'leagues'} |
| `/api/rest/dashboard/apps/regions/^(?P<pk>[^/.]+)/countries/(?P<country_id>[^/.]+)/leagues\.(?P<format>[a-z0-9]+)/?$` | `region-leagues` | `api.rest.dashboard.apps.region.views.RegionViewSet` {'get': 'leagues', 'post': 'leagues'} |
| `/api/rest/dashboard/apps/regions/^(?P<pk>[^/.]+)/countries/(?P<country_id>[^/.]+)/leagues/(?P<league_id>[^/.]+)/teams/(?P<team_id>[^/.]+)/$` | `region-team-detail` | `api.rest.dashboard.apps.region.views.RegionViewSet` {'get': 'team_detail', 'put': 'team_detail', 'patch': 'team_detail', 'delete': 'team_detail'} |
| `/api/rest/dashboard/apps/regions/^(?P<pk>[^/.]+)/countries/(?P<country_id>[^/.]+)/leagues/(?P<league_id>[^/.]+)/teams/(?P<team_id>[^/.]+)\.(?P<format>[a-z0-9]+)/?$` | `region-team-detail` | `api.rest.dashboard.apps.region.views.RegionViewSet` {'get': 'team_detail', 'put': 'team_detail', 'patch': 'team_detail', 'delete': 'team_detail'} |
| `/api/rest/dashboard/apps/regions/^(?P<pk>[^/.]+)/countries/(?P<country_id>[^/.]+)/leagues/(?P<league_id>[^/.]+)/teams/$` | `region-teams` | `api.rest.dashboard.apps.region.views.RegionViewSet` {'get': 'teams', 'post': 'teams'} |
| `/api/rest/dashboard/apps/regions/^(?P<pk>[^/.]+)/countries/(?P<country_id>[^/.]+)/leagues/(?P<league_id>[^/.]+)/teams\.(?P<format>[a-z0-9]+)/?$` | `region-teams` | `api.rest.dashboard.apps.region.views.RegionViewSet` {'get': 'teams', 'post': 'teams'} |
| `/api/rest/dashboard/apps/regions/` | `api-root` | `rest_framework.routers.APIRootView`  |
| `/api/rest/dashboard/apps/regions/<drf_format_suffix:format>` | `api-root` | `rest_framework.routers.APIRootView`  |
| `/api/rest/dashboard/schema/` | `schema` | `drf_spectacular.views.SpectacularAPIView`  |
| `/api/rest/dashboard/schema/swagger-ui/` | `swagger-ui` | `drf_spectacular.views.SpectacularSwaggerView`  |
| `/api/rest/dashboard/schema/redoc/` | `redoc` | `drf_spectacular.views.SpectacularRedocView`  |

## Tasks, signals and operator entry points

Static definitions include dormant modules. `AppConfig.ready()` import evidence and missing registrations are discussed in the architecture document; a decorator alone does not prove runtime registration.

| Source | Definitions / imports |
|---|---|
| `app/apps/accounts/receivers.py` | receive_podcast_viewed @receiver(podcast_viewed) |
| `app/apps/accounts/signals.py` | user_registered = Signal(); user_logged_in = Signal() |
| `app/apps/match/signals.py` | create_match_event @receiver(post_save, sender=Match) |
| `app/apps/media/audio/management/commands/__init__.py` | No top-level definitions (inspect imports/comments) |
| `app/apps/media/audio/management/commands/rotate_cloud_front_cookies.py` | Command |
| `app/apps/media/audio/receivers.py` | audio_post_save @receiver(post_save, sender=Audio) |
| `app/apps/media/audio/tasks.py` | BaseTaskWithRetry; rotate_cloud_front_cookies @shared_task(base=BaseTaskWithRetry, bind=True, name='CloudFront Audio HLS Signing Task'); process_audio @shared_task(base=BaseTaskWithRetry, bind=True, name='Audio Processing Pipeline') |
| `app/apps/media/images/receivers.py` | image_post_save_receiver @receiver(post_save, sender=Image) |
| `app/apps/media/offline/management/commands/__init__.py` | No top-level definitions (inspect imports/comments) |
| `app/apps/media/offline/management/commands/expire_licenses.py` | Command |
| `app/apps/media/offline/management/commands/gc_orphaned_packages.py` | Command |
| `app/apps/media/offline/management/commands/revoke_inactive_licenses.py` | Command |
| `app/apps/media/offline/tasks.py` | get_package_status; _derive_keys_from_dek; build_offline_package_streaming @shared_task(bind=True); build_offline_package_task @shared_task(bind=True) |
| `app/apps/media/receivers.py` | profile_post_save @receiver(post_save, sender=User) |
| `app/apps/media/transcription/receivers.py` | create_transcription_quota @receiver(models.signals.post_save, sender=User) |
| `app/apps/memberships/receivers.py` | on_entitlement_changed @receiver(post_save, sender=Entitlement) @receiver(post_delete, sender=Entitlement); on_subscription_changed @receiver(post_save, sender=Subscription) @receiver(post_delete, sender=Subscription) |
| `app/apps/persons/receivers.py` | player_post_save @receiver(post_save, sender=Player) |
| `app/apps/posts/podcasts/management/commands/__init__.py` | No top-level definitions (inspect imports/comments) |
| `app/apps/posts/podcasts/management/commands/audit_podcast_content.py` | Command |
| `app/apps/posts/podcasts/management/commands/recalculate_trending.py` | Command |
| `app/apps/posts/podcasts/receivers.py` | invalidate_user_recommendations_receiver @receiver(post_save, sender=PlayBack) |
| `app/apps/posts/podcasts/signals.py` | podcast_viewed = Signal() |
| `app/apps/posts/podcasts/tasks.py` | BaseTaskWithRetry; recalc_episode_trending @shared_task(bind=True, base=BaseTaskWithRetry, name='Recalculate Trending Episodes') |
| `app/apps/promotions/receivers.py` | No top-level definitions (inspect imports/comments) |
| `app/apps/queue/signals.py` | merge_anon_queue_to_user @receiver(user_logged_in) |
| `app/apps/recommendation/management/commands/__init__.py` | No top-level definitions (inspect imports/comments) |
| `app/apps/recommendation/management/commands/generate_dataset.py` | Command |
| `app/apps/recommendation/management/commands/recalc_user_affinity.py` | Command |
| `app/apps/recommendation/management/commands/train_recommenders.py` | _ensure_faiss; Command |
| `app/apps/recommendation/tasks.py` | recalc_user_category_affinity_postgres @shared_task(bind=True) |
| `app/apps/region/leagues/clubs/receivers.py` | team_code_generate_fn @receiver(pre_save, sender=Team) |
| `app/apps/region/leagues/receivers.py` | league_code_generate_fn @receiver(pre_save, sender=League) |
| `app/apps/region/receivers.py` | generate_code_for_region @receiver(pre_save, sender=Region); generate_code_for_country @receiver(post_save, sender=Country) |
| `app/apps/tactics/management/commands/__init__.py` | No top-level definitions (inspect imports/comments) |
| `app/apps/tactics/management/commands/prepopulate_lineup_positions.py` | Command |
| `app/apps/tactics/receiver.py` | my_handler @receiver(m2m_changed, sender=Formation.lineup.through) |
| `app/helpers/tasks.py` | delay_on_commit |

## Test modules

Static test method counts are not test execution counts; discovery and execution results are recorded in [baseline-validation.md](baseline-validation.md). Empty legacy modules provide no coverage.

| Module | Test methods/functions |
|---|---|
| `app/api/rest/dashboard/apps/podcasts/tests.py` | 18 |
| `app/api/rest/web/apps/media/offline/tests.py` | 8 |
| `app/api/rest/web/apps/media/streaming/tests.py` | 22 |
| `app/api/rest/web/apps/podcasts/tests.py` | 10 |
| `app/api/rest/web/serializers/test_auth.py` | 2 |
| `app/api/rest/web/serializers/test_authentication.py` | 13 |
| `app/apps/billing/tests.py` | 12 |
| `app/apps/comments/tests.py` | 0 |
| `app/apps/forum/tests.py` | 0 |
| `app/apps/media/audio/tests.py` | 4 |
| `app/apps/media/offline/tests.py` | 5 |
| `app/apps/media/providers/tests.py` | 20 |
| `app/apps/media/test_delivery_service.py` | 20 |
| `app/apps/media/test_upload_finalization.py` | 19 |
| `app/apps/media/test_upload_intents.py` | 13 |
| `app/apps/media/tests.py` | 7 |
| `app/apps/memberships/tests.py` | 29 |
| `app/apps/posts/podcasts/test_audit_podcast_content_command.py` | 4 |
| `app/apps/posts/podcasts/test_content_migration.py` | 7 |
| `app/apps/posts/podcasts/test_publication_migration.py` | 1 |
| `app/apps/posts/podcasts/tests.py` | 17 |
| `app/apps/posts/tests.py` | 0 |
| `app/apps/queue/tests.py` | 14 |
| `app/conf/settings/test.py` | 0 |
| `app/conf/test_health.py` | 4 |
| `app/conf/test_runner.py` | 0 |
| `app/conf/test_schema.py` | 1 |
| `app/conf/tests.py` | 25 |

Inventory totals: 67 app registrations; 88 repository models (including proxies); 49 repository migrations; 174 non-admin URL leaves.

## Dependency inventory

`uv.lock` resolves 187 package entries, including optional worker/dev extras. SF-00 installed 117 distributions for the default + dev environment. This table inventories declared dependencies; optional worker entries were not exercised. The pinned Git source for `pycflare[storages,media]` is `f214c80de3843d47f0593386a60169c77e8bc801`.

| Group | Declared requirement | Locked version |
|---|---|---|
| default | `babel` | 2.18.0 |
| default | `celery[redis]` | 5.6.3 |
| default | `clerk-backend-api` | 7.0.0 |
| default | `cryptography` | 50.0.1 |
| default | `django>=5.2.7,<6.0` | 5.2.17 |
| default | `django-celery-beat` | 2.9.0 |
| default | `django-clerk-sdk>=1.0.0,<2.0` | 1.0.0 |
| default | `django-cors-headers` | 4.9.0 |
| default | `django-filter` | 26.1 |
| default | `django-guardian` | 3.4.0 |
| default | `djangorestframework>=3.16.1` | 3.18.0 |
| default | `ffmpeg-python` | 0.2.0 |
| default | `httpx` | 0.28.1 |
| default | `pillow` | 12.3.0 |
| default | `python-decouple` | 3.8 |
| default | `redis` | 6.4.0 |
| default | `requests` | 2.34.2 |
| default | `django-celery-results>=2.6.0` | 2.6.0 |
| default | `boto3>=1.42.41` | 1.43.82 |
| default | `python-multipart>=0.0.22` | 0.0.32 |
| default | `prometheus-client>=0.24.1` | 0.26.0 |
| default | `django-redis>=6.0.0` | 7.0.0 |
| default | `honcho>=2.0.0` | 2.0.0 |
| default | `channels>=4.3.2` | 4.3.2 |
| default | `channels-redis>=4.3.0` | 4.3.0 |
| default | `pyyaml>=6.0.3` | 6.0.3 |
| default | `gevent>=25.9.1` | 26.8.0 |
| default | `psycopg[binary,pool]>=3.3.2` | 3.3.4 |
| default | `drf-spectacular>=0.29.0` | 0.30.0 |
| default | `drf-spectacular-sidecar>=2026.1.1` | 2026.8.1 |
| default | `dj-database-url>=3.1.2` | 3.1.2 |
| default | `pycflare[storages,media] @ git+https://github.com/Leydotpy/pycflare.git@f214c80de3843d47f0593386a60169c77e8bc801` | 0.0.1 |
| media-workers | `google-cloud-speech>=2.36.0` | 2.40.0 |
| media-workers | `google-cloud-storage>=3.9.0` | 3.13.1 |
| media-workers | `openai>=2.16.0` | 3.5.0 |
| media-workers | `torch>=2.10.0` | 2.13.0 |
| media-workers | `whisper-openai>=1.0.0` | 1.0.0 |
| recommendation-workers | `faiss-cpu>=1.13.2` | 1.15.0 |
| recommendation-workers | `joblib>=1.5.3` | 1.5.3 |
| recommendation-workers | `numpy>=2.3.5` | 2.5.2 |
| recommendation-workers | `pandas>=2.3.3` | 3.0.5 |
| recommendation-workers | `scikit-learn>=1.8.0` | 1.9.0 |
| recommendation-workers | `scipy>=1.17.0` | 1.18.1 |
| dev | `celery-types>=0.24.0` | 0.26.0 |
| dev | `coverage[toml]>=7.10.0` | 7.15.4 |
| dev | `djangorestframework-stubs>=3.16.6` | 3.18.1 |
| dev | `mypy>=1.17.0` | 2.3.1 |
| dev | `pip-audit>=2.9.0` | 2.10.1 |
| dev | `ruff>=0.12.0` | 0.16.5 |

## Abstract model bases

These bases do not own separate tables; inherited relations appear on the concrete model rows above.

| Model | Source | Relations contributed |
|---|---|---|
| `apps.analytics.models.AbstractAnalytics` | `app/apps/analytics/models.py` | countries → region.Country (ManyToManyField); competitions → leagues.League (ManyToManyField); regions → region.Region (ManyToManyField); teams → clubs.Team (ManyToManyField); players → persons.Player (ManyToManyField); matches → match.Match (ManyToManyField); subscribers → users.ClerkUser (ManyToManyField); view_logs → analytics.ObjectView (GenericRelation) |
| `apps.persons.models.Person` | `app/apps/persons/models.py` | nations → region.Country (ManyToManyField) |
| `apps.posts.models.BasePost` | `app/apps/posts/models.py` | parent → self (ForeignKey) |
| `apps.promotions.models.LinkedPromotion` | `app/apps/promotions/models.py` | content_type → contenttypes.ContentType (ForeignKey); content_object → generic target (GenericForeignKey) |
| `apps.promotions.models.AbstractPromotion` | `app/apps/promotions/models.py` | keywords → promotions.KeywordPromotion (GenericRelation); pages → promotions.PagePromotion (GenericRelation) |
| `apps.promotions.models.AbstractPostList` | `app/apps/promotions/models.py` | keywords → promotions.KeywordPromotion (GenericRelation); pages → promotions.PagePromotion (GenericRelation) |

## Celery registration probe

Django setup plus `conf.celery.app.autodiscover_tasks(force=True)` registered all six repository tasks listed in the architecture document. The affinity beat target is registered. The four beat entries targeting `django.core.management.call_command` are not registered. This probe performs imports only; it does not dispatch tasks or connect to a broker.
