# django_podcast_pipeline.py
import hashlib
import os

import django
import pandas as pd
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db.models import Count, Max, Q
from django.db.models.functions import Coalesce

from apps.comments.models import Comment
# Import your models AFTER django.setup()
from apps.posts.podcasts.models import Podcast, PostReaction, Episode, PlayBack

# If running standalone:
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "your_project.settings")
# django.setup()
# Attempt to import Comment from a likely path in your repo.
# Primary guess: apps.posts.comments.models; fallback: apps.comments.models

#########################################
# Reaction / Comment weight mapping     #
#########################################
REACTION_WEIGHT = {
    "like": 1.0,
    "love": 2.0,
    "happy": 1.0,
    "sad": -0.5,
    "angry": -1.0,
    "funny": 0.5,
    "dislike": -1.0,
}

# weights for comment types (tune these values to taste)
COMMENT_WEIGHT = {
    "comment_text": 1.0,
    "comment_image": 1.5,
    "comment_sticker": 0.5,
}


def reaction_to_weight(r):
    """Map reaction or comment token to a numeric weight."""
    if not r:
        return 0.0
    if r in REACTION_WEIGHT:
        return REACTION_WEIGHT[r]
    if r in COMMENT_WEIGHT:
        return COMMENT_WEIGHT[r]
    return 0.0


#########################################
# Utilities                             #
#########################################
def df_from_queryset(qs):
    rows = list(qs)
    return pd.DataFrame.from_records(rows) if rows else pd.DataFrame()


def list_to_token_string(prefix, ids):
    """Return sorted token string 'prefix_id1|prefix_id2' or '' if empty."""
    if not ids:
        return ""
    s = "|".join(f"{prefix}_{i}" for i in sorted(ids))
    return s


def stable_fingerprint(parts) -> str:
    payload = repr(parts).encode("utf-8")
    return hashlib.sha1(payload).hexdigest()


def build_relation_lookup(through_model, source_field: str, target_field: str, source_ids):
    mapping = {}
    if not source_ids:
        return mapping

    for source_id, target_id in through_model.objects.filter(
        **{f"{source_field}__in": source_ids}
    ).values_list(source_field, target_field):
        mapping.setdefault(source_id, []).append(target_id)
    return mapping


#########################################
# LOAD: attributes (rich M2M features)  #
#########################################
def build_attributes_df():
    """
    Build podcast-level DataFrame that includes:
      - CONFIG_ID (podcast.id)
      - title, structure, slug, parent_id, subtitle
      - TEAM_IDS, PLAYER_IDS, LEAGUE_IDS, COUNTRY_IDS, REGION_IDS, MATCH_IDS
      - PODCAST_PLAY_COUNT, UNIQUE_LISTENERS, LAST_PLAYED (if Views exist)
      - ATTRIBUTES: hashed token of structured features
    """
    podcasts_qs = (
        Podcast.objects
        .annotate(
            play_count=Coalesce(Count("episodes__playback", distinct=False), 0),
            unique_listeners=Coalesce(
                Count("episodes__playback__user", filter=Q(episodes__playback__user__isnull=False), distinct=True),
                0,
            ),
            last_played=Max("episodes__playback__last_played_at"),
        )
        .all()
    )

    podcasts = list(podcasts_qs)
    podcast_ids = [podcast.id for podcast in podcasts]
    team_lookup = build_relation_lookup(Podcast.teams.through, "podcast_id", "team_id", podcast_ids)
    player_lookup = build_relation_lookup(Podcast.players.through, "podcast_id", "player_id", podcast_ids)
    league_lookup = build_relation_lookup(Podcast.competitions.through, "podcast_id", "league_id", podcast_ids)
    country_lookup = build_relation_lookup(Podcast.countries.through, "podcast_id", "country_id", podcast_ids)
    region_lookup = build_relation_lookup(Podcast.regions.through, "podcast_id", "region_id", podcast_ids)
    match_lookup = build_relation_lookup(Podcast.matches.through, "podcast_id", "match_id", podcast_ids)

    records = []
    for p in podcasts:
        team_ids = team_lookup.get(p.id, [])
        player_ids = player_lookup.get(p.id, [])
        league_ids = league_lookup.get(p.id, [])
        country_ids = country_lookup.get(p.id, [])
        region_ids = region_lookup.get(p.id, [])
        match_ids = match_lookup.get(p.id, [])

        team_tokens = list_to_token_string("team", team_ids)
        player_tokens = list_to_token_string("player", player_ids)
        league_tokens = list_to_token_string("league", league_ids)
        country_tokens = list_to_token_string("country", country_ids)
        region_tokens = list_to_token_string("region", region_ids)
        match_tokens = list_to_token_string("match", match_ids)

        fingerprint_tuple = (
            tuple(sorted(team_ids)),
            tuple(sorted(player_ids)),
            tuple(sorted(league_ids)),
            p.structure if hasattr(p, "structure") else "",
        )
        attr_hash = stable_fingerprint(fingerprint_tuple)

        records.append({
            "CONFIG_ID": p.id,
            "title": getattr(p, "title", None),
            "structure": getattr(p, "structure", None),
            "slug": getattr(p, "slug", None),
            "parent_id": getattr(p, "parent_id", None),
            "subtitle": getattr(p, "subtitle", None),
            "duration": getattr(p, "duration", None),
            "view_count": getattr(p, "view_count", 0),

            "TEAM_IDS": team_ids,
            "PLAYER_IDS": player_ids,
            "LEAGUE_IDS": league_ids,
            "COUNTRY_IDS": country_ids,
            "REGION_IDS": region_ids,
            "MATCH_IDS": match_ids,

            "TEAM_TOKENS": team_tokens,
            "PLAYER_TOKENS": player_tokens,
            "LEAGUE_TOKENS": league_tokens,
            "COUNTRY_TOKENS": country_tokens,
            "REGION_TOKENS": region_tokens,
            "MATCH_TOKENS": match_tokens,

            "PODCAST_PLAY_COUNT": getattr(p, "play_count", 0) or 0,
            "UNIQUE_LISTENERS": getattr(p, "unique_listeners", 0) or 0,
            "LAST_PLAYED": getattr(p, "last_played", None),

            "ATTRIBUTES": attr_hash,
        })

    attributes_df = pd.DataFrame.from_records(records)
    for c in ["PODCAST_PLAY_COUNT", "UNIQUE_LISTENERS"]:
        if c in attributes_df.columns:
            attributes_df[c] = attributes_df[c].astype("float32")
    return attributes_df


#########################################
# LOAD: interactions (PostReaction + Comment)
#########################################
def build_interactions_df():
    """
    Build interactions DataFrame combining:
      - PostReaction rows targeting Podcast
      - Comment rows targeting Podcast (with comment metadata)
    Canonical columns in the returned DF:
      - id, CONFIG_ID, CUSTOMER_ID, reaction, TIMES, WEIGHT, PARENT_ID, COMMENT_LENGTH
    """
    podcast_ct = ContentType.objects.get_for_model(Podcast)

    # --- Reactions ---
    reactions_qs = (
        PostReaction.objects
        .filter(content_type=podcast_ct)
        .select_related("user")
        .values("id", "object_id", "user_id", "reaction", "timestamp")
    )
    reactions_df = df_from_queryset(reactions_qs)
    if not reactions_df.empty:
        reactions_df.rename(columns={"object_id": "CONFIG_ID", "user_id": "CUSTOMER_ID", "timestamp": "TIMES"},
                            inplace=True)
        # add placeholder columns so concat keeps schema consistent
        reactions_df["PARENT_ID"] = pd.NA
        reactions_df["COMMENT_LENGTH"] = pd.NA
    else:
        reactions_df = pd.DataFrame(
            columns=["id", "CONFIG_ID", "CUSTOMER_ID", "reaction", "TIMES", "PARENT_ID", "COMMENT_LENGTH"])

    # --- Comments ---
    comments_df = pd.DataFrame()
    if Comment is not None:
        comments_qs = (
            Comment.objects
            .filter(content_type=podcast_ct)
            .select_related("user")
            .values("id", "object_id", "user_id", "comment_type", "content", "timestamp", "parent_id")
        )
        comments_df = df_from_queryset(comments_qs)
        if not comments_df.empty:
            # Map comment_type -> reaction-like token: e.g. "comment_text"
            # some comment_type values may already be 'text'/'image' etc.
            comments_df["reaction"] = comments_df["comment_type"].apply(
                lambda t: f"comment_{t}" if pd.notna(t) else "comment_text"
            )
            comments_df.rename(columns={"object_id": "CONFIG_ID", "user_id": "CUSTOMER_ID", "timestamp": "TIMES"},
                               inplace=True)
            # Compute comment length (characters)
            comments_df["content"] = comments_df.get("content", "").fillna("")
            comments_df["COMMENT_LENGTH"] = comments_df["content"].astype(str).str.len().astype("float32")
            # Keep parent_id so we can compute reply counts
            comments_df["PARENT_ID"] = comments_df.get("parent_id", pd.NA)
            # Keep canonical columns only
            comments_df = comments_df[
                ["id", "CONFIG_ID", "CUSTOMER_ID", "reaction", "TIMES", "PARENT_ID", "COMMENT_LENGTH"]]
        else:
            comments_df = pd.DataFrame(
                columns=["id", "CONFIG_ID", "CUSTOMER_ID", "reaction", "TIMES", "PARENT_ID", "COMMENT_LENGTH"])
    else:
        # No Comment model available: create empty DF with proper columns (user should fix import path)
        comments_df = pd.DataFrame(
            columns=["id", "CONFIG_ID", "CUSTOMER_ID", "reaction", "TIMES", "PARENT_ID", "COMMENT_LENGTH"])

    # --- Concat interactions ---
    interactions_df = pd.concat([reactions_df, comments_df], ignore_index=True, sort=False)

    if interactions_df.empty:
        interactions_df = pd.DataFrame(
            columns=["id", "CONFIG_ID", "CUSTOMER_ID", "reaction", "TIMES", "WEIGHT", "PARENT_ID", "COMMENT_LENGTH"])
        return interactions_df

    # Compute weight for both reaction rows and comment rows
    interactions_df["WEIGHT"] = interactions_df["reaction"].map(reaction_to_weight).astype("float32")

    # Ensure TIMES is datetime if not already
    if "TIMES" in interactions_df.columns:
        interactions_df["TIMES"] = pd.to_datetime(interactions_df["TIMES"], errors="coerce")

    # Normalize parent column
    if "PARENT_ID" in interactions_df.columns:
        # convert to numeric where possible
        interactions_df["PARENT_ID"] = pd.to_numeric(interactions_df["PARENT_ID"], errors="coerce").astype("float32")

    # COMMENT_LENGTH already set for comments; ensure numeric
    if "COMMENT_LENGTH" in interactions_df.columns:
        interactions_df["COMMENT_LENGTH"] = pd.to_numeric(interactions_df["COMMENT_LENGTH"], errors="coerce")

    return interactions_df


#########################################
# BUILD popularity_df (aggregates)      #
#########################################
def build_popularity_df(attributes_df, interactions_df):
    """
    Combine play metrics from attributes_df and reaction/comment aggregates from interactions_df
    Result columns include:
      - CONFIG_ID
      - PODCAST_PLAY_COUNT, UNIQUE_LISTENERS, LAST_PLAYED (from attributes_df)
      - TOTAL_REACTIONS, AVG_REACTION_WEIGHT
      - TOTAL_COMMENTS, REPLY_COUNT, AVG_COMMENT_LENGTH
      - reaction/comment type counts: LIKE_COUNT, COMMENT_TEXT_COUNT, etc.
    """
    pop = attributes_df[["CONFIG_ID", "PODCAST_PLAY_COUNT", "UNIQUE_LISTENERS", "LAST_PLAYED"]].copy()

    if interactions_df.empty:
        pop["TOTAL_REACTIONS"] = 0.0
        pop["AVG_REACTION_WEIGHT"] = 0.0
        pop["TOTAL_COMMENTS"] = 0.0
        pop["REPLY_COUNT"] = 0.0
        pop["AVG_COMMENT_LENGTH"] = 0.0
        for r in list(REACTION_WEIGHT.keys()) + list(COMMENT_WEIGHT.keys()):
            # e.g. "comment_text" -> "COMMENT_TEXT_COUNT"
            col = r.upper() if not r.startswith("comment_") else r.replace("comment_", "COMMENT_").upper()
            pop[f"{col}_COUNT"] = 0.0
        return pop

    # Overall aggregates
    agg = interactions_df.groupby("CONFIG_ID").agg(
        TOTAL_REACTIONS=("id", "count"),
        AVG_REACTION_WEIGHT=("WEIGHT", "mean")
    ).reset_index()

    # Pivot by token (includes comment_* tokens)
    pivot = interactions_df.pivot_table(index="CONFIG_ID", columns="reaction", values="id", aggfunc="count",
                                        fill_value=0)
    pivot = pivot.reset_index()
    # Normalize pivot column names ("like" -> "LIKE_COUNT", "comment_text" -> "COMMENT_TEXT_COUNT")
    pivot.columns = [c if c == "CONFIG_ID" else f"{c.upper()}_COUNT" for c in pivot.columns]

    pop = pop.merge(agg, on="CONFIG_ID", how="left").merge(pivot, on="CONFIG_ID", how="left")

    # Total comments: sum of any COMMENT_*_COUNT columns in pivot
    comment_cols = [col for col in pop.columns if col.startswith("COMMENT_") and col.endswith("_COUNT")]
    if comment_cols:
        pop["TOTAL_COMMENTS"] = pop[comment_cols].sum(axis=1).astype("float32")
    else:
        pop["TOTAL_COMMENTS"] = 0.0

    # Compute REPLY_COUNT: count of comments with non-null PARENT_ID
    if "PARENT_ID" in interactions_df.columns:
        replies = interactions_df.dropna(subset=["PARENT_ID"])
        if not replies.empty:
            reply_agg = replies.groupby("CONFIG_ID").agg(REPLY_COUNT=("id", "count")).reset_index()
            pop = pop.merge(reply_agg, on="CONFIG_ID", how="left")
        else:
            pop["REPLY_COUNT"] = 0.0
    else:
        pop["REPLY_COUNT"] = 0.0

    # Compute AVG_COMMENT_LENGTH: mean length across comment rows
    if "COMMENT_LENGTH" in interactions_df.columns:
        comment_lengths = interactions_df[
            interactions_df["reaction"].astype(str).str.startswith("comment_") & interactions_df[
                "COMMENT_LENGTH"].notna()]
        if not comment_lengths.empty:
            length_agg = comment_lengths.groupby("CONFIG_ID").agg(
                AVG_COMMENT_LENGTH=("COMMENT_LENGTH", "mean")).reset_index()
            pop = pop.merge(length_agg, on="CONFIG_ID", how="left")
        else:
            pop["AVG_COMMENT_LENGTH"] = 0.0
    else:
        pop["AVG_COMMENT_LENGTH"] = 0.0

    pop.fillna({"TOTAL_REACTIONS": 0, "AVG_REACTION_WEIGHT": 0, "TOTAL_COMMENTS": 0, "REPLY_COUNT": 0,
                "AVG_COMMENT_LENGTH": 0}, inplace=True)
    for c in ["TOTAL_REACTIONS", "AVG_REACTION_WEIGHT", "TOTAL_COMMENTS", "REPLY_COUNT", "AVG_COMMENT_LENGTH"]:
        if c in pop.columns:
            pop[c] = pop[c].astype("float32")

    # Ensure reaction/comment count columns exist for every reaction/comment type
    for r in REACTION_WEIGHT.keys():
        col = f"{r.upper()}_COUNT"
        if col not in pop.columns:
            pop[col] = 0.0
        else:
            pop[col] = pop[col].astype("float32")
    for ct in COMMENT_WEIGHT.keys():
        # ct e.g. "comment_text" -> "COMMENT_TEXT_COUNT"
        col = f"{ct.upper()}_COUNT"
        if col not in pop.columns:
            pop[col] = 0.0
        else:
            pop[col] = pop[col].astype("float32")

    return pop


#########################################
# Glue: produce final DataFrames        #
#########################################
def load_from_db_as_dfs():
    attributes_df = build_attributes_df()
    interactions_df = build_interactions_df()
    popularity_df = build_popularity_df(attributes_df, interactions_df)
    return attributes_df, interactions_df, popularity_df


#########################################
# Example usage (standalone)            #
#########################################
if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "conf.settings")
    django.setup()

    attrs, inters, pops = load_from_db_as_dfs()
    print("attributes:", attrs.shape)
    print("interactions:", inters.shape)
    print("popularity:", pops.shape)

    OUTPUT_DIR = getattr(settings, "RECOMMENDER_OUTPUT_PATH")

    if not OUTPUT_DIR.exists():
        OUTPUT_DIR.mkdir(parents=True)

    attrs.to_csv(OUTPUT_DIR / "podcast_attributes.csv", index=False)
    inters.to_csv(OUTPUT_DIR / "podcast_interactions.csv", index=False)
    pops.to_csv(OUTPUT_DIR / "podcast_popularity.csv", index=False)
