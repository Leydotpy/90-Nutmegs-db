import os
from collections import Counter
from datetime import datetime, timezone

import django
import numpy as np
import pandas as pd
import tensorflow as tf

from core.compat import get_user_model

# Import your db-backed builders if available; otherwise these assume you have
# attributes_df, interactions_df and popularity_df already in the environment.
# from your_app.data_builders import build_attributes_df, build_interactions_df, build_popularity_df
# from apps.accounts.models import Account

User = get_user_model()

# If running standalone:
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "your_project.settings")
# django.setup()
###############################
# Configurable parameters
###############################
TOP_K_TEAMS = 200
TOP_K_PLAYERS = 200
TOP_K_LEAGUES = 100
SEQ_LEN = 10  # length of history sequence to build per-interaction
RECENCY_BUCKETS = [1, 7, 30, 365]  # days boundaries for recency bins


###############################
# 0. Utility helpers
###############################
def ensure_list_col(df, col):
    """Ensure column exists and is list-like (empty list if missing)."""
    if col not in df.columns:
        df[col] = [[] for _ in range(len(df))]
    else:
        df[col] = df[col].apply(lambda x: x if isinstance(x, (list, tuple)) else ([] if pd.isna(x) else [x]))


def top_k_tokens_from_listcol(df, list_col, k):
    """Return top-k tokens (ids) across rows where list_col contains lists of ints."""
    ensure_list_col(df, list_col)
    cnt = Counter()
    for lst in df[list_col].values:
        cnt.update(lst)
    topk = [item for item, _ in cnt.most_common(k)]
    return topk


def build_token_to_index_map(topk):
    return {tok: idx + 1 for idx, tok in enumerate(topk)}  # reserve 0 for OOV / padding


def list_to_multi_hot(lst, token_index_map, k):
    """Return length-k numpy array multi-hot given list of ids and token->index map."""
    vec = np.zeros(k, dtype=np.int32)
    if not lst:
        return vec
    for tok in lst:
        idx = token_index_map.get(tok)
        if idx is not None and 1 <= idx <= k:
            # map idx->position idx-1
            vec[idx - 1] = 1
    return vec


def now_utc_ts():
    return datetime.now(timezone.utc)


###############################
# 1) Build top-k multi-hot columns
###############################
def add_topk_multihot_features(attributes_df, interactions_df, top_k_teams=TOP_K_TEAMS, top_k_players=TOP_K_PLAYERS,
                               top_k_leagues=TOP_K_LEAGUES):
    """
    Input:
      - attributes_df must contain TEAM_IDS, PLAYER_IDS, LEAGUE_IDS as lists per row (podcast-level)
    Output:
      - attributes_df extended with TEAM_MULTI_HOT, PLAYER_MULTI_HOT, LEAGUE_MULTI_HOT (np arrays)
      - a token->index mapping dict for each entity type (useful at inference)
    """
    # Ensure list columns exist
    for col in ["TEAM_IDS", "PLAYER_IDS", "LEAGUE_IDS"]:
        ensure_list_col(attributes_df, col)

    # Compute top-k tokens from attributes (global frequency)
    topk_teams = top_k_tokens_from_listcol(attributes_df, "TEAM_IDS", top_k_teams)
    topk_players = top_k_tokens_from_listcol(attributes_df, "PLAYER_IDS", top_k_players)
    topk_leagues = top_k_tokens_from_listcol(attributes_df, "LEAGUE_IDS", top_k_leagues)

    team_map = build_token_to_index_map(topk_teams)
    player_map = build_token_to_index_map(topk_players)
    league_map = build_token_to_index_map(topk_leagues)

    # Create multi-hot columns (np arrays)
    attributes_df["TEAM_MULTI_HOT"] = attributes_df["TEAM_IDS"].apply(
        lambda lst: list_to_multi_hot(lst, team_map, len(topk_teams)))
    attributes_df["PLAYER_MULTI_HOT"] = attributes_df["PLAYER_IDS"].apply(
        lambda lst: list_to_multi_hot(lst, player_map, len(topk_players)))
    attributes_df["LEAGUE_MULTI_HOT"] = attributes_df["LEAGUE_IDS"].apply(
        lambda lst: list_to_multi_hot(lst, league_map, len(topk_leagues)))

    # Return attributes_df and maps
    maps = {"team_map": team_map, "player_map": player_map, "league_map": league_map, "team_k": len(topk_teams),
            "player_k": len(topk_players), "league_k": len(topk_leagues), }
    return attributes_df, maps


###############################
# 4) Merge Account metadata into interactions_df
###############################
def merge_account_metadata(interactions_df):
    """
    Merge Account metadata (prefer clerk_user_id then email) into interactions_df and produce CUSTOMER_CODE
    """
    # Load accounts
    accounts_qs = User.objects.all().values("id", "clerk_user_id", "email", "username")
    accounts_df = pd.DataFrame.from_records(list(accounts_qs))
    if accounts_df.empty:
        interactions_df["CUSTOMER_CODE"] = interactions_df["CUSTOMER_ID"].astype(str)
        return interactions_df

    accounts_df.rename(columns={"id": "CUSTOMER_ID"}, inplace=True)
    # prefer clerk_user_id then email then username then id
    accounts_df["CUSTOMER_CODE"] = accounts_df["clerk_user_id"].fillna(accounts_df["email"]).fillna(
        accounts_df["username"]).fillna(accounts_df["CUSTOMER_ID"].astype(str))
    # merge
    interactions_df = interactions_df.merge(accounts_df[["CUSTOMER_ID", "CUSTOMER_CODE"]], on="CUSTOMER_ID", how="left")
    # fallback
    interactions_df["CUSTOMER_CODE"] = interactions_df["CUSTOMER_CODE"].fillna(
        interactions_df["CUSTOMER_ID"].astype(str))
    return interactions_df


###############################
# 3) Temporal features & user histories
###############################
def add_temporal_and_history_features(interactions_df, attributes_df, seq_len=SEQ_LEN, now_ts=None):
    """
    - Merge attributes_df (to get LAST_PLAYED per podcast)
    - Compute time_since_last_played (seconds)
    - Compute recency bucket w.r.t LAST_PLAYED (days -> bucket id)
    - Build user history sequences: for each interaction row, history is previous SEQ_LEN CONFIG_IDs (padded left with 0)
    Returns interactions_df with added columns:
       - TIME_SINCE_LAST_PLAYED (float seconds)
       - RECENCY_BUCKET (int index)
       - HISTORY_IDS (np.array of length seq_len)
       - HISTORY_LEN (int)
    """

    if now_ts is None:
        now_dt = now_utc_ts()
    else:
        now_dt = now_ts

    # Prepare attributes index by CONFIG_ID for fast lookup
    attr_small = attributes_df.set_index("CONFIG_ID")[
        ["LAST_PLAYED"]].copy() if "LAST_PLAYED" in attributes_df.columns else pd.DataFrame(columns=["LAST_PLAYED"])
    # reset index if empty
    if not attr_small.empty:
        attr_small["LAST_PLAYED"] = pd.to_datetime(attr_small["LAST_PLAYED"]).dt.tz_localize(None)
    # Merge LAST_PLAYED
    interactions_df = interactions_df.merge(attr_small, left_on="CONFIG_ID", right_index=True, how="left")

    # Convert TIMES to datetime
    interactions_df["TIMES_DT"] = pd.to_datetime(interactions_df["TIMES"], unit="ns", errors="coerce") if np.issubdtype(
        interactions_df["TIMES"].dtype, np.number) else pd.to_datetime(interactions_df["TIMES"], errors="coerce")

    # TIME_SINCE_LAST_PLAYED: seconds between interaction and LAST_PLAYED (or large number if missing)
    def compute_time_since_last_played(row):
        if pd.isna(row["LAST_PLAYED"]):
            # if podcast has no last played timestamp, compute since epoch or use large delta from now
            return float((now_dt - (row["TIMES_DT"] or now_dt)).total_seconds())
        else:
            return float(((row["TIMES_DT"] or now_dt) - row["LAST_PLAYED"]).total_seconds())

    interactions_df["TIME_SINCE_LAST_PLAYED"] = interactions_df.apply(compute_time_since_last_played, axis=1)

    # ensure now_dt is timezone-naive or consistent with your timestamps
    now_dt = datetime.now(timezone.utc)  # or datetime.utcnow() if your timestamps are naive

    # make sure TIMES_DT exists and is datetime
    interactions_df["TIMES_DT"] = pd.to_datetime(interactions_df["TIMES"], errors="coerce")

    # make sure LAST_PLAYED exists and is datetime (it came from attributes merge)
    if "LAST_PLAYED" in interactions_df.columns:
        interactions_df["LAST_PLAYED"] = pd.to_datetime(interactions_df["LAST_PLAYED"], errors="coerce")
    else:
        interactions_df["LAST_PLAYED"] = pd.NaT

    # Vectorized computation:
    # interaction_time = TIMES_DT if present else now_dt
    interaction_time = interactions_df["TIMES_DT"].fillna(pd.Timestamp(now_dt))

    # time_since = interaction_time - LAST_PLAYED (seconds). For rows where LAST_PLAYED is missing,
    # fall back to now_dt - interaction_time (i.e., how long since interaction until now).
    time_since = (interaction_time - interactions_df["LAST_PLAYED"]).dt.total_seconds()

    # For rows with missing LAST_PLAYED, compute (now - interaction_time)
    mask_missing_last = interactions_df["LAST_PLAYED"].isna()
    if mask_missing_last.any():
        time_since.loc[mask_missing_last] = (
                pd.Timestamp(now_dt) - interaction_time.loc[mask_missing_last]).dt.total_seconds()

    # Fill any remaining NaN with 0 and cast to float32 numpy array
    interactions_df["TIME_SINCE_LAST_PLAYED"] = time_since.fillna(0.0).astype("float32")
    # If you later need a numpy array:
    time_since_last_played = interactions_df["TIME_SINCE_LAST_PLAYED"].to_numpy(dtype="float32")

    # Recency bucket: days between TIMES_DT and LAST_PLAYED (use abs days)
    def recency_bucket_from_seconds(sec):
        days = abs(sec) / 86400.0
        for i, bound in enumerate(RECENCY_BUCKETS):
            if days <= bound:
                return i  # bucket index
        return len(RECENCY_BUCKETS)

    interactions_df["RECENCY_BUCKET"] = interactions_df["TIME_SINCE_LAST_PLAYED"].apply(
        recency_bucket_from_seconds).astype("int32")

    # Build user histories: for each customer, sort by time ascending and create previous seq_len item ids
    interactions_df.sort_values(by=["CUSTOMER_ID", "TIMES_DT"], ascending=[True, True], inplace=True)
    interactions_df.reset_index(drop=True, inplace=True)

    # We'll create HISTORY_IDS (np array) and HISTORY_LEN
    history_ids_list = []
    history_len_list = []

    # per-user rolling window
    grouped = interactions_df.groupby("CUSTOMER_ID", sort=False)
    for customer_id, group in grouped:
        # for each group, iterate rows and keep prior items
        prior_items = []
        for idx, row in group.iterrows():
            # build the history of prior_items (most recent last)
            hist = prior_items[-seq_len:] if len(prior_items) >= seq_len else prior_items[:]  # list of ints
            # pad left with 0s to length seq_len
            pad = [0] * (seq_len - len(hist))
            hist_padded = pad + hist
            history_ids_list.append(np.array(hist_padded, dtype=np.int32))
            history_len_list.append(len(hist))
            # then append current item to prior_items for next rows
            prior_items.append(int(row["CONFIG_ID"]))
    # assign results back (aligned because we iterated in groupby sorted order which matches interactions_df order)
    interactions_df["HISTORY_IDS"] = history_ids_list
    interactions_df["HISTORY_LEN"] = history_len_list

    return interactions_df


###############################
# 2) Build tf.data.Dataset
###############################
def build_tf_dataset(interactions_df, attributes_df, maps, seq_len=SEQ_LEN):
    """
    Build a tf.data.Dataset suitable for training a ranking or retrieval model.
    Features included (example):
      - user_id (int), item_id (int), weight (float), times (float),
      - team_multi_hot, player_multi_hot, league_multi_hot (fixed arrays)
      - history_ids (seq_len ints), history_len (int)
      - time_since_last_played (float), recency_bucket (int)
    Label: WEIGHT (you can adjust)
    """

    if interactions_df.empty:
        raise ValueError("interactions_df is empty")

    # Merge item-level multi-hot features from attributes_df into interactions_df
    # attributes_df should contain TEAM_MULTI_HOT, PLAYER_MULTI_HOT, LEAGUE_MULTI_HOT
    item_feats = attributes_df.set_index("CONFIG_ID")[["TEAM_MULTI_HOT", "PLAYER_MULTI_HOT", "LEAGUE_MULTI_HOT"]].copy()
    # Expand into arrays
    interactions_merged = interactions_df.merge(item_feats, left_on="CONFIG_ID", right_index=True, how="left")

    # Replace missing multi-hot with zeros
    team_k = maps.get("team_k", 0)
    player_k = maps.get("player_k", 0)
    league_k = maps.get("league_k", 0)

    if "TEAM_MULTI_HOT" not in interactions_merged.columns:
        interactions_merged["TEAM_MULTI_HOT"] = [np.zeros(team_k, dtype=np.int32) for _ in
                                                 range(len(interactions_merged))]
    if "PLAYER_MULTI_HOT" not in interactions_merged.columns:
        interactions_merged["PLAYER_MULTI_HOT"] = [np.zeros(player_k, dtype=np.int32) for _ in
                                                   range(len(interactions_merged))]
    if "LEAGUE_MULTI_HOT" not in interactions_merged.columns:
        interactions_merged["LEAGUE_MULTI_HOT"] = [np.zeros(league_k, dtype=np.int32) for _ in
                                                   range(len(interactions_merged))]

    # Prepare numpy arrays for each feature
    user_ids = interactions_merged["CUSTOMER_ID"].astype("int32").to_numpy()
    item_ids = interactions_merged["CONFIG_ID"].astype("int32").to_numpy()
    weights = interactions_merged["WEIGHT"].astype("float32").to_numpy()
    times = pd.to_datetime(interactions_merged["TIMES"]).astype("int64").fillna(0).to_numpy()  # ns since epoch

    # Stack multi-hot arrays
    team_multi = np.stack(interactions_merged["TEAM_MULTI_HOT"].apply(
        lambda x: np.asarray(x, dtype=np.int32)).to_list()) if team_k > 0 else np.zeros((len(interactions_merged), 0),
                                                                                        dtype=np.int32)
    player_multi = np.stack(interactions_merged["PLAYER_MULTI_HOT"].apply(
        lambda x: np.asarray(x, dtype=np.int32)).to_list()) if player_k > 0 else np.zeros((len(interactions_merged), 0),
                                                                                          dtype=np.int32)
    league_multi = np.stack(interactions_merged["LEAGUE_MULTI_HOT"].apply(
        lambda x: np.asarray(x, dtype=np.int32)).to_list()) if league_k > 0 else np.zeros((len(interactions_merged), 0),
                                                                                          dtype=np.int32)

    # Histories
    history_ids = np.stack(interactions_merged["HISTORY_IDS"].apply(lambda x: np.asarray(x, dtype=np.int32)).to_list())
    history_len = interactions_merged["HISTORY_LEN"].astype("int32").to_numpy()

    # Time & recency features
    time_since_last_played = interactions_merged["TIME_SINCE_LAST_PLAYED"].astype("float32").to_numpy()
    recency_bucket = interactions_merged["RECENCY_BUCKET"].astype("int32").to_numpy()

    # CUSTOMER_CODE optional text field (we will not include as numeric feature by default)
    if "CUSTOMER_CODE" in interactions_merged.columns:
        customer_codes = interactions_merged["CUSTOMER_CODE"].astype(str).to_numpy()
    else:
        customer_codes = None

    # Prepare features dict
    features = {"user_id": user_ids, "item_id": item_ids, "time": times, "team_multi": team_multi,
                "player_multi": player_multi, "league_multi": league_multi, "history_ids": history_ids,
                "history_len": history_len, "time_since_last_played": time_since_last_played,
                "recency_bucket": recency_bucket, }
    # Label example: WEIGHT (engagement)
    labels = weights

    # Convert to tf.data.Dataset
    ds = tf.data.Dataset.from_tensor_slices((features, labels))
    # shuffle & batch as needed by training loop
    return ds


###############################
# Wrapper: run full pipeline
###############################
def run_full_feature_pipeline(attributes_df=None, interactions_df=None, popularity_df=None):
    """
    If attributes_df / interactions_df not passed, attempt to build them from DB via helper functions
    (you should provide build_attributes_df / build_interactions_df from prior pipeline)
    """
    # If not provided, try to call builders (uncomment if you have them)
    if attributes_df is None or interactions_df is None or popularity_df is None:
        # attempt to import or call your previously-defined builders
        try:
            from .builder import build_attributes_df, build_interactions_df, build_popularity_df
            attributes_df_local = build_attributes_df() if attributes_df is None else attributes_df
            interactions_df_local = build_interactions_df() if interactions_df is None else interactions_df
            popularity_df_local = build_popularity_df(attributes_df_local,
                                                      interactions_df_local) if popularity_df is None else popularity_df
        except Exception as e:
            raise RuntimeError(
                "attributes_df / interactions_df not provided and automatic builders not available. Provide DataFrames or add build_* implementations.") from e
    else:
        attributes_df_local = attributes_df
        interactions_df_local = interactions_df
        popularity_df_local = popularity_df

    # (1) top-k multi-hot features
    attributes_df_local, maps = add_topk_multihot_features(attributes_df_local, interactions_df_local)

    # (4) merge account metadata
    interactions_df_local = merge_account_metadata(interactions_df_local)

    # (3) temporal & history features
    interactions_df_local = add_temporal_and_history_features(interactions_df_local, attributes_df_local,
                                                              seq_len=SEQ_LEN)

    # (2) build tf dataset
    tf_ds = build_tf_dataset(interactions_df_local, attributes_df_local, maps, seq_len=SEQ_LEN)

    return {"attributes_df": attributes_df_local, "interactions_df": interactions_df_local,
            "popularity_df": popularity_df_local, "maps": maps, "tf_dataset": tf_ds}


###############################
# Example usage snippet
###############################
if __name__ == "__main__":
    # If running standalone ensure Django is setup
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "conf.settings")
    django.setup()

    # If you already have builders, call them:
    # from your_app.data_builders import build_attributes_df, build_interactions_df, build_popularity_df
    # attrs, inters, pops = build_attributes_df(), build_interactions_df(), build_popularity_df(...)

    # For demonstration I'll try to use the previously implemented builders if present
    try:
        from core.recommender.datasets.builder import build_attributes_df, build_interactions_df, build_popularity_df

        attrs = build_attributes_df()
        inters = build_interactions_df()
        pops = build_popularity_df(attrs, inters)
    except Exception as e:
        print(e)
        raise RuntimeError(
            "Please provide attributes_df, interactions_df, popularity_df or add the build_* functions to your project.")

    outputs = run_full_feature_pipeline(attrs, inters, pops)
    print("Done. Shapes:")
    print("attributes:", outputs["attributes_df"].shape)
    print("interactions:", outputs["interactions_df"].shape)
    print("popularity:", outputs["popularity_df"].shape)
    print("tf_dataset example element:")
    for elem in outputs["tf_dataset"].take(1):
        print(elem)
